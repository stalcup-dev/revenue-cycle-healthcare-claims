from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import pandas as pd
from google.cloud import bigquery


SUMMARY_SQL = """
WITH base AS (
  SELECT
    CAST(clm_id AS STRING) AS claim_id,
    'MEDICARE_FFS_PROXY' AS payer,
    DATE_SUB(CURRENT_DATE(), INTERVAL CAST(COALESCE(aging_days, 0) AS INT64) DAY) AS service_date,
    COALESCE(top_denial_group, top_denial_prcsg, 'UNSPECIFIED') AS denial_reason_raw,
    LOWER(
      CONCAT(
        COALESCE(top_denial_group, ''),
        ' ',
        COALESCE(top_next_best_action, ''),
        ' ',
        COALESCE(top_denial_prcsg, '')
      )
    ) AS denial_reason_text,
    COALESCE(top_denial_group, 'UNSPECIFIED') AS facility_or_service_line,
    COALESCE(top_denial_prcsg, '') AS denial_code,
    COALESCE(denied_potential_allowed_proxy_amt, 0.0) AS denied_amount,
    COALESCE(p_denial, 0.0) AS p_denial
  FROM `{source_fqn}`
),
denied AS (
  SELECT
    *,
    (
      p_denial > 0
      OR denial_code != ''
      OR denial_reason_raw != 'UNSPECIFIED'
      OR denied_amount > 0
    ) AS denial_flag
  FROM base
),
bucketed AS (
  SELECT
    *,
    CASE
      WHEN REGEXP_CONTAINS(denial_reason_text, r'auth|authorization|precert|elig|eligibility|coverage|member') THEN 'AUTH_ELIG'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'coding|modifier|dx|icd|cpt|documentation|medical record|bundl') THEN 'CODING_DOC'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'timely|filing|limit|late') THEN 'TIMELY_FILING'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'duplicate|dup') THEN 'DUPLICATE'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'contract|noncovered|non-covered|bundled per contract|write off') THEN 'CONTRACTUAL'
      ELSE 'OTHER_PROXY'
    END AS denial_bucket
  FROM denied
  WHERE denial_flag
),
weighted AS (
  SELECT
    *,
    CASE
      WHEN denial_bucket IN ('AUTH_ELIG', 'CODING_DOC', 'TIMELY_FILING', 'DUPLICATE') THEN 1.0
      WHEN denial_bucket = 'CONTRACTUAL' THEN 0.2
      ELSE 0.6
    END AS preventability_weight
  FROM bucketed
)
SELECT
  denial_bucket,
  denial_reason_raw AS denial_reason,
  payer,
  SUM(denied_amount) AS denied_amount_sum,
  COUNT(*) AS denial_count,
  SAFE_DIVIDE(SUM(denied_amount), COUNT(*)) AS avg_denied_amount,
  ANY_VALUE(preventability_weight) AS preventability_weight,
  SUM(denied_amount) * ANY_VALUE(preventability_weight) AS priority_score
FROM weighted
GROUP BY 1, 2, 3
ORDER BY priority_score DESC
LIMIT @summary_limit
"""


WORKQUEUE_SQL = """
WITH base AS (
  SELECT
    CAST(clm_id AS STRING) AS claim_id,
    'MEDICARE_FFS_PROXY' AS payer,
    DATE_SUB(CURRENT_DATE(), INTERVAL CAST(COALESCE(aging_days, 0) AS INT64) DAY) AS service_date,
    COALESCE(top_denial_group, top_denial_prcsg, 'UNSPECIFIED') AS denial_reason_raw,
    LOWER(
      CONCAT(
        COALESCE(top_denial_group, ''),
        ' ',
        COALESCE(top_next_best_action, ''),
        ' ',
        COALESCE(top_denial_prcsg, '')
      )
    ) AS denial_reason_text,
    COALESCE(top_denial_group, 'UNSPECIFIED') AS facility_or_service_line,
    COALESCE(top_denial_prcsg, '') AS denial_code,
    COALESCE(denied_potential_allowed_proxy_amt, 0.0) AS denied_amount,
    COALESCE(p_denial, 0.0) AS p_denial
  FROM `{source_fqn}`
),
denied AS (
  SELECT
    *,
    (
      p_denial > 0
      OR denial_code != ''
      OR denial_reason_raw != 'UNSPECIFIED'
      OR denied_amount > 0
    ) AS denial_flag
  FROM base
),
bucketed AS (
  SELECT
    *,
    CASE
      WHEN REGEXP_CONTAINS(denial_reason_text, r'auth|authorization|precert|elig|eligibility|coverage|member') THEN 'AUTH_ELIG'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'coding|modifier|dx|icd|cpt|documentation|medical record|bundl') THEN 'CODING_DOC'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'timely|filing|limit|late') THEN 'TIMELY_FILING'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'duplicate|dup') THEN 'DUPLICATE'
      WHEN REGEXP_CONTAINS(denial_reason_text, r'contract|noncovered|non-covered|bundled per contract|write off') THEN 'CONTRACTUAL'
      ELSE 'OTHER_PROXY'
    END AS denial_bucket
  FROM denied
  WHERE denial_flag
),
weighted AS (
  SELECT
    *,
    CASE
      WHEN denial_bucket IN ('AUTH_ELIG', 'CODING_DOC', 'TIMELY_FILING', 'DUPLICATE') THEN 1.0
      WHEN denial_bucket = 'CONTRACTUAL' THEN 0.2
      ELSE 0.6
    END AS preventability_weight
  FROM bucketed
)
SELECT
  claim_id,
  payer,
  service_date,
  denial_reason_raw AS denial_reason,
  denial_bucket,
  denied_amount,
  preventability_weight,
  denied_amount * preventability_weight AS row_priority,
  CASE
    WHEN denial_bucket = 'AUTH_ELIG' THEN 'Eligibility/Auth team'
    WHEN denial_bucket = 'CODING_DOC' THEN 'Coding/CDI'
    WHEN denial_bucket = 'TIMELY_FILING' THEN 'Billing'
    WHEN denial_bucket = 'DUPLICATE' THEN 'Billing'
    WHEN denial_bucket = 'CONTRACTUAL' THEN 'Contracting/RCM lead'
    ELSE 'RCM analyst review'
  END AS owner,
  CASE
    WHEN denial_bucket = 'AUTH_ELIG' THEN 'Verify eligibility/auth; obtain auth; rebill'
    WHEN denial_bucket = 'CODING_DOC' THEN 'Coding review; validate modifiers/diagnoses; resubmit'
    WHEN denial_bucket = 'TIMELY_FILING' THEN 'Validate filing date; appeal if eligible; write-off if expired'
    WHEN denial_bucket = 'DUPLICATE' THEN 'Confirm duplicate; adjust/void as needed'
    WHEN denial_bucket = 'CONTRACTUAL' THEN 'Confirm contract terms; route non-recoverable to write-off policy'
    ELSE 'Manual triage; classify reason; assign owner'
  END AS next_action,
  CASE
    WHEN denial_bucket = 'AUTH_ELIG' THEN 'Auth number, eligibility response'
    WHEN denial_bucket = 'CODING_DOC' THEN 'Coding notes, op note, medical record excerpt'
    WHEN denial_bucket = 'TIMELY_FILING' THEN 'Filing limit, submission timestamps'
    WHEN denial_bucket = 'DUPLICATE' THEN 'Claim history, matching identifiers'
    WHEN denial_bucket = 'CONTRACTUAL' THEN 'Contract excerpt, allowed schedule'
    ELSE 'Denial reason detail, line notes, routing owner'
  END AS evidence_needed
FROM weighted
ORDER BY row_priority DESC
LIMIT @workqueue_size
"""


def _fmt_money(value: float) -> str:
    return f"${value:,.0f}"


def _column_mapping_md() -> str:
    return "\n".join(
        [
            "| Conceptual field | Source column used | Notes |",
            "|---|---|---|",
            "| claim_id | `clm_id` | direct claim identifier |",
            "| payer | constant `MEDICARE_FFS_PROXY` | payer detail unavailable in selected mart |",
            "| denial_flag | derived from `p_denial/top_denial_prcsg/top_denial_group/denied_potential_allowed_proxy_amt` | deterministic OR-rule |",
            "| denial_reason | `top_denial_group` fallback `top_denial_prcsg` | proxy reason when detailed reason absent |",
            "| denied_amount | `denied_potential_allowed_proxy_amt` | proxy denied amount |",
            "| service_date | `DATE_SUB(CURRENT_DATE(), INTERVAL aging_days DAY)` | estimated service date proxy |",
            "| facility_or_service_line | `top_denial_group` | service-line proxy |",
        ]
    )


def _brief_markdown(
    source_fqn: str,
    summary_df: pd.DataFrame,
    workqueue_df: pd.DataFrame,
    workqueue_size: int,
) -> str:
    top2 = summary_df.head(2)
    top5 = summary_df.head(5)
    total_priority = float(summary_df["priority_score"].sum()) if not summary_df.empty else 0.0
    top2_priority = float(top2["priority_score"].sum()) if not top2.empty else 0.0
    top2_share = (top2_priority / total_priority * 100.0) if total_priority > 0 else 0.0
    status = "LIMITED_CONTEXT"
    reason = (
        "Payer and denial reason are proxy fields in this mart; use this brief for directional triage and owner routing."
    )

    top5_lines: list[str] = []
    for _, row in top5.iterrows():
        top5_lines.append(
            f"- `{row['denial_bucket']}` / `{row['denial_reason']}` / `{row['payer']}`: "
            f"{_fmt_money(float(row['denied_amount_sum']))} across {int(row['denial_count'])} claims "
            f"(priority {_fmt_money(float(row['priority_score']))})."
        )

    owner_lines: list[str] = []
    if not workqueue_df.empty:
        owner_counts = (
            workqueue_df.groupby("owner", as_index=False)
            .size()
            .sort_values("size", ascending=False)
            .head(5)
        )
        for _, row in owner_counts.iterrows():
            owner_lines.append(f"- {row['owner']}: {int(row['size'])} claims in the top {workqueue_size}.")

    lines = [
        "# Denials Triage Brief v1",
        "",
        f"Source relation: `{source_fqn}` (dbt-transformed mart only).",
        "",
        "## Decision",
        f"Focus this week on the top 2 denial buckets by priority score (covers {top2_share:.1f}% of weighted denial exposure).",
        "",
        "## Status + Reason",
        f"- Status: {status}",
        f"- Reason: {reason}",
        "",
        "## Top drivers (priority-ranked)",
        *top5_lines,
        "",
        "## This week actions (reversible)",
        "- Validate top denial buckets against sample claim evidence before scaling any process changes.",
        "- Route top workqueue items to owner queues with evidence requirements attached.",
        "- Re-run this triage next cycle and compare top-2 stability before committing irreversible workflow changes.",
        "",
        f"## Workqueue ({workqueue_size} claims)",
        f"- Output: [`exports/denials_workqueue_v1.csv`](../exports/denials_workqueue_v1.csv)",
        f"- Summary: [`exports/denials_triage_summary_v1.csv`](../exports/denials_triage_summary_v1.csv)",
        *owner_lines,
        "",
        "## Falsification",
        "If next cycle the top-2 buckets do not remain in the top set or weighted exposure shifts materially, we change focus and re-prioritize.",
        "",
        "## Column mapping (required conceptual fields)",
        _column_mapping_md(),
        "",
        "Note: Denial reason and denied dollar values may be proxies depending on available columns in the selected mart.",
    ]
    return "\n".join(lines) + "\n"


def _run_query(client: bigquery.Client, sql: str, params: list[bigquery.ScalarQueryParameter]) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(sql, job_config=job_config).result().to_dataframe()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build denials triage summary + workqueue from a single dbt BigQuery relation.")
    parser.add_argument("--project", default=os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "rcm-flagship")
    parser.add_argument("--dataset", default=os.getenv("BQ_DATASET_ID") or "rcm")
    parser.add_argument("--relation", default="mart_workqueue_claims")
    parser.add_argument("--out", default="exports")
    parser.add_argument("--workqueue-size", type=int, default=25)
    parser.add_argument("--summary-limit", type=int, default=50)
    parser.add_argument("--dry-run-sql", action="store_true", help="Print SQL statements only; do not execute.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_fqn = f"{args.project}.{args.dataset}.{args.relation}"

    summary_sql = SUMMARY_SQL.format(source_fqn=source_fqn)
    workqueue_sql = WORKQUEUE_SQL.format(source_fqn=source_fqn)

    if args.dry_run_sql:
        print("-- SOURCE RELATION --")
        print(source_fqn)
        print("\n-- SUMMARY SQL --")
        print(summary_sql)
        print("\n-- WORKQUEUE SQL --")
        print(workqueue_sql)
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    client = bigquery.Client(project=args.project)

    summary_df = _run_query(
        client,
        summary_sql,
        [bigquery.ScalarQueryParameter("summary_limit", "INT64", args.summary_limit)],
    )
    workqueue_df = _run_query(
        client,
        workqueue_sql,
        [bigquery.ScalarQueryParameter("workqueue_size", "INT64", args.workqueue_size)],
    )

    summary_path = out_dir / "denials_triage_summary_v1.csv"
    workqueue_path = out_dir / "denials_workqueue_v1.csv"
    brief_path = docs_dir / "denials_triage_brief_v1.md"

    summary_df.to_csv(summary_path, index=False)
    workqueue_df.to_csv(workqueue_path, index=False)
    brief_path.write_text(_brief_markdown(source_fqn, summary_df, workqueue_df, args.workqueue_size), encoding="utf-8")

    print(f"SOURCE_RELATION={source_fqn}")
    print(f"SOURCE_GRAIN=claim-level ({args.relation})")
    print(f"WROTE={summary_path}")
    print(f"WROTE={workqueue_path}")
    print(f"WROTE={brief_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
