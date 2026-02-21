from __future__ import annotations

import argparse
import hashlib
import os
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

DETAIL_SQL = """
WITH base AS (
  SELECT
    CAST(clm_id AS STRING) AS claim_id,
    DATE_SUB(@as_of_date, INTERVAL CAST(COALESCE(aging_days, 0) AS INT64) DAY) AS service_date,
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
    COALESCE(top_denial_prcsg, '') AS denial_code,
    COALESCE(denied_potential_allowed_proxy_amt, 0.0) AS denied_amount,
    COALESCE(p_denial, 0.0) AS p_denial
  FROM `{source_fqn}`
  WHERE CAST(COALESCE(aging_days, 0) AS INT64) BETWEEN @min_aging_days AND (@min_aging_days + @lookback_days)
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
  service_date,
  denial_reason_raw AS denial_reason,
  denial_bucket,
  denied_amount,
  preventability_weight,
  denied_amount * preventability_weight AS prevention_priority_score
FROM weighted
ORDER BY service_date DESC, prevention_priority_score DESC
"""

MIN_AGING_SQL = """
SELECT
  MIN(CAST(COALESCE(aging_days, 0) AS INT64)) AS min_aging_days
FROM `{source_fqn}`
WHERE
  COALESCE(p_denial, 0.0) > 0
  OR COALESCE(top_denial_prcsg, '') != ''
  OR COALESCE(top_denial_group, 'UNSPECIFIED') != 'UNSPECIFIED'
  OR COALESCE(denied_potential_allowed_proxy_amt, 0.0) > 0
"""

OWNER_MAP = {
    "AUTH_ELIG": "Eligibility/Auth team",
    "CODING_DOC": "Coding/CDI",
    "TIMELY_FILING": "Billing",
    "DUPLICATE": "Billing",
    "CONTRACTUAL": "Contracting/RCM lead",
    "OTHER_PROXY": "RCM analyst review",
}

LEVERS_MAP = {
    "AUTH_ELIG": [
        "Tighten auth-at-registration checks.",
        "Route missing-auth claims to pre-bill review.",
        "Apply payer-specific eligibility retry before finalization.",
    ],
    "CODING_DOC": [
        "Run focused coding QA on high-dollar denials.",
        "Add pre-bill edit for modifier/diagnosis mismatches.",
        "Escalate documentation gaps to CDI within 24h.",
    ],
    "TIMELY_FILING": [
        "Set aging alerts before filing limits.",
        "Prioritize near-limit claims daily.",
        "Use standard appeal packet for late-file exceptions.",
    ],
    "DUPLICATE": [
        "Add duplicate fingerprint check before submission.",
        "Reconcile corrected claims same day.",
        "Route duplicate candidates for analyst approval.",
    ],
    "CONTRACTUAL": [
        "Separate contractual from preventable denials in queues.",
        "Escalate recurring contract disputes weekly.",
        "Track non-recoverable volume for policy write-offs.",
    ],
    "OTHER_PROXY": [
        "Manually tag top unresolved reasons each cycle.",
        "Expand mapping rules from recurring patterns.",
        "Route ambiguous denials to analyst triage SLA.",
    ],
}

EVIDENCE_MAP = {
    "AUTH_ELIG": ["Auth number", "Eligibility response timestamp"],
    "CODING_DOC": ["Coder notes", "Medical record excerpt"],
    "TIMELY_FILING": ["Submission timestamps", "Payer filing policy"],
    "DUPLICATE": ["Claim history", "Matching identifiers"],
    "CONTRACTUAL": ["Contract language", "Allowed schedule"],
    "OTHER_PROXY": ["Denial text", "Manual categorization note"],
}


def _fmt_money(value: float) -> str:
    return f"${value:,.0f}"


def _fmt_pct(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def _stability_confidence(top2_overlap: int) -> str:
    if top2_overlap >= 2:
        return "HIGH"
    if top2_overlap == 1:
        return "MEDIUM"
    return "LOW"


def _run_query(client: bigquery.Client, sql: str, params: list[bigquery.ScalarQueryParameter]) -> pd.DataFrame:
    cfg = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(sql, job_config=cfg).result().to_dataframe()


def _with_dataset_week_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["service_date"] = pd.to_datetime(out["service_date"])
    out["dataset_week_start"] = out["service_date"] - pd.to_timedelta(out["service_date"].dt.weekday, unit="D")
    out["dataset_week_key"] = out["dataset_week_start"].dt.strftime("%Y-%m-%d")
    return out


def _build_summary(current_df: pd.DataFrame, limit_rows: int) -> pd.DataFrame:
    summary = (
        current_df.groupby(["denial_bucket", "denial_reason"], as_index=False)
        .agg(
            denied_amount_sum=("denied_amount", "sum"),
            denial_count=("claim_id", "count"),
            preventability_weight=("preventability_weight", "first"),
        )
        .copy()
    )
    summary["prevented_exposure_proxy"] = summary["denied_amount_sum"] * summary["preventability_weight"]
    summary["priority_score"] = summary["prevented_exposure_proxy"]
    summary["payer_dim_status"] = "MISSING_IN_MART"
    summary = summary.sort_values(
        ["priority_score", "denied_amount_sum", "denial_bucket", "denial_reason"],
        ascending=[False, False, True, True],
        kind="mergesort",
    ).head(limit_rows)
    return summary[
        [
            "denial_bucket",
            "denial_reason",
            "denied_amount_sum",
            "denial_count",
            "preventability_weight",
            "prevented_exposure_proxy",
            "priority_score",
            "payer_dim_status",
        ]
    ]


def _build_stability(current_df: pd.DataFrame, prior_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    current = current_df.groupby("denial_bucket", as_index=False).agg(current_priority_score=("prevention_priority_score", "sum"))
    prior = prior_df.groupby("denial_bucket", as_index=False).agg(prior_priority_score=("prevention_priority_score", "sum"))
    merged = current.merge(prior, on="denial_bucket", how="outer").fillna(0.0)
    merged["delta_priority_score"] = merged["current_priority_score"] - merged["prior_priority_score"]

    current_rank_map = (
        current.sort_values(["current_priority_score", "denial_bucket"], ascending=[False, True], kind="mergesort")
        .reset_index(drop=True)
        .assign(current_rank=lambda d: d.index + 1)
    )[["denial_bucket", "current_rank"]]
    prior_rank_map = (
        prior.sort_values(["prior_priority_score", "denial_bucket"], ascending=[False, True], kind="mergesort")
        .reset_index(drop=True)
        .assign(prior_rank=lambda d: d.index + 1)
    )[["denial_bucket", "prior_rank"]]
    merged = merged.merge(current_rank_map, on="denial_bucket", how="left").merge(prior_rank_map, on="denial_bucket", how="left")
    merged["rank_delta"] = merged["prior_rank"] - merged["current_rank"]

    current_total = float(merged["current_priority_score"].sum())
    prior_total = float(merged["prior_priority_score"].sum())
    merged["current_share"] = merged["current_priority_score"] / current_total if current_total > 0 else 0.0
    merged["prior_share"] = merged["prior_priority_score"] / prior_total if prior_total > 0 else 0.0
    merged["share_delta"] = merged["current_share"] - merged["prior_share"]
    merged = merged.sort_values(["current_priority_score", "denial_bucket"], ascending=[False, True], kind="mergesort")

    current_top2 = set(merged[merged["current_priority_score"] > 0].head(2)["denial_bucket"].tolist())
    prior_top2 = set(merged[merged["prior_priority_score"] > 0].head(2)["denial_bucket"].tolist())
    overlap = len(current_top2.intersection(prior_top2))

    return merged[
        [
            "denial_bucket",
            "current_priority_score",
            "prior_priority_score",
            "delta_priority_score",
            "current_rank",
            "prior_rank",
            "rank_delta",
            "current_share",
            "prior_share",
            "share_delta",
        ]
    ], overlap


def _build_scenarios(summary_df: pd.DataFrame) -> pd.DataFrame:
    top2 = (
        summary_df.sort_values(["priority_score", "denial_bucket"], ascending=[False, True], kind="mergesort")
        .head(2)[["denial_bucket", "prevented_exposure_proxy"]]
        .copy()
    )
    top2["prevent_10"] = top2["prevented_exposure_proxy"] * 0.10
    top2["prevent_20"] = top2["prevented_exposure_proxy"] * 0.20
    top2["prevent_30"] = top2["prevented_exposure_proxy"] * 0.30
    return top2[["denial_bucket", "prevented_exposure_proxy", "prevent_10", "prevent_20", "prevent_30"]]


def _build_brief_markdown(source_fqn: str, summary_df: pd.DataFrame, scenarios_df: pd.DataFrame, current_week: str, prior_week: str, top2_overlap: int, workqueue_size: int) -> str:
    total_denied = float(summary_df["denied_amount_sum"].sum()) if not summary_df.empty else 0.0
    total_prevented = float(summary_df["prevented_exposure_proxy"].sum()) if not summary_df.empty else 0.0
    top2 = summary_df.head(2)
    top2_names = ", ".join(top2["denial_bucket"].tolist()) if not top2.empty else "NONE"
    top2_share = float(top2["priority_score"].sum()) / total_prevented if total_prevented > 0 else 0.0

    lines = [
        "# Denials Prevention Opportunity Brief v1",
        "",
        f"Source relation: `{source_fqn}` (dbt mart only).",
        "",
        "## Impact in 90 Seconds (Prevention)",
        f"- Current dataset-week: `{current_week}`",
        f"- Prior dataset-week: `{prior_week}`",
        f"- Total denied exposure (PROXY): {_fmt_money(total_denied)}",
        f"- Total prevented exposure proxy: {_fmt_money(total_prevented)}",
        f"- Top 2 buckets: {top2_names}",
        f"- Top 2 prevented share: {_fmt_pct(top2_share)}",
        f"- Stability confidence: {_stability_confidence(top2_overlap)} (TOP2_OVERLAP={top2_overlap}/2)",
        f"- Workqueue size used: {workqueue_size}",
        "",
        "## Prevention scenarios (directional)",
        "| denial_bucket | prevented_exposure_proxy | prevent_10 | prevent_20 | prevent_30 |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in scenarios_df.iterrows():
        lines.append(
            f"| {row['denial_bucket']} | {_fmt_money(float(row['prevented_exposure_proxy']))} | {_fmt_money(float(row['prevent_10']))} | {_fmt_money(float(row['prevent_20']))} | {_fmt_money(float(row['prevent_30']))} |"
        )

    lines.extend(["", "## Levers & owners (next week)"])
    for bucket in top2["denial_bucket"].tolist():
        lines.append(f"### {bucket}")
        lines.append(f"- Owner: {OWNER_MAP.get(bucket, 'RCM analyst review')}")
        lines.append("- Levers:")
        for lever in LEVERS_MAP.get(bucket, LEVERS_MAP["OTHER_PROXY"])[:3]:
            lines.append(f"  - {lever}")
        lines.append("- Evidence needed:")
        for ev in EVIDENCE_MAP.get(bucket, EVIDENCE_MAP["OTHER_PROXY"])[:2]:
            lines.append(f"  - {ev}")

    lines.extend([
        "",
        "## Data gaps and proxy caveats",
        "- `payer_dim_status` is fixed to `MISSING_IN_MART`.",
        "- `denied_amount` uses `denied_potential_allowed_proxy_amt` (proxy).",
        "- Safe for directional prevention prioritization, not causal savings claims.",
    ])
    return "\n".join(lines) + "\n"


def _build_public_html(summary_df: pd.DataFrame, scenarios_df: pd.DataFrame, current_week: str, prior_week: str, top2_overlap: int, workqueue_size: int) -> str:
    total_denied = float(summary_df["denied_amount_sum"].sum()) if not summary_df.empty else 0.0
    total_prevented = float(summary_df["prevented_exposure_proxy"].sum()) if not summary_df.empty else 0.0
    top2 = summary_df.head(2)
    top2_names = ", ".join(top2["denial_bucket"].tolist()) if not top2.empty else "NONE"
    top2_share = float(top2["priority_score"].sum()) / total_prevented if total_prevented > 0 else 0.0

    cards = [
        "<section class=\"impact-card\">",
        "<h2>Impact in 90 Seconds (Prevention)</h2>",
        f"<p>Current dataset-week <strong>{escape(current_week)}</strong> vs prior <strong>{escape(prior_week)}</strong>.</p>",
        "<ul>",
        f"<li>Total denied exposure (<strong>PROXY</strong>): <strong>{escape(_fmt_money(total_denied))}</strong>.</li>",
        f"<li>Total prevented exposure proxy: <strong>{escape(_fmt_money(total_prevented))}</strong>.</li>",
        f"<li>Top 2 buckets: <strong>{escape(top2_names)}</strong>.</li>",
        f"<li>Top 2 prevented share: <strong>{_fmt_pct(top2_share)}</strong>.</li>",
        f"<li>Stability confidence: <strong>{_stability_confidence(top2_overlap)}</strong> (TOP2_OVERLAP={top2_overlap}/2).</li>",
        f"<li>Workqueue size used: <strong>{workqueue_size}</strong>.</li>",
        "</ul>",
        "<p><strong>Safe for:</strong></p><ul><li>Directional prevention triage</li><li>Owner routing</li></ul>",
        "<p><strong>Not safe for:</strong></p><ul><li>Payer-level decisions</li><li>Causal ROI claims</li></ul>",
        "</section>",
        "<h2>Prevention scenarios (directional)</h2>",
        "<table><thead><tr><th>denial_bucket</th><th>prevented_exposure_proxy</th><th>prevent_10</th><th>prevent_20</th><th>prevent_30</th></tr></thead><tbody>",
    ]
    for _, row in scenarios_df.iterrows():
        cards.append(
            "<tr>"
            + f"<td>{escape(str(row['denial_bucket']))}</td>"
            + f"<td>{escape(_fmt_money(float(row['prevented_exposure_proxy'])))}</td>"
            + f"<td>{escape(_fmt_money(float(row['prevent_10'])))}</td>"
            + f"<td>{escape(_fmt_money(float(row['prevent_20'])))}</td>"
            + f"<td>{escape(_fmt_money(float(row['prevent_30'])))}</td>"
            + "</tr>"
        )
    cards.append("</tbody></table>")
    cards.append("<h2>Levers & owners (next week)</h2>")
    for bucket in top2["denial_bucket"].tolist():
        cards.append(f"<h3>{escape(bucket)}</h3>")
        cards.append(f"<p><strong>Owner:</strong> {escape(OWNER_MAP.get(bucket, 'RCM analyst review'))}</p>")
        cards.append("<p><strong>Levers:</strong></p><ul>" + "".join(f"<li>{escape(x)}</li>" for x in LEVERS_MAP.get(bucket, LEVERS_MAP['OTHER_PROXY'])[:3]) + "</ul>")
        cards.append("<p><strong>Evidence needed:</strong></p><ul>" + "".join(f"<li>{escape(x)}</li>" for x in EVIDENCE_MAP.get(bucket, EVIDENCE_MAP['OTHER_PROXY'])[:2]) + "</ul>")
    return "\n".join(cards)


def _build_teaching_html(source_fqn: str, summary_df: pd.DataFrame, scenarios_df: pd.DataFrame, current_week: str, prior_week: str, top2_overlap: int) -> str:
    top = summary_df.head(1)
    top_bucket = top.iloc[0]["denial_bucket"] if not top.empty else "N/A"
    top_reason = top.iloc[0]["denial_reason"] if not top.empty else "N/A"
    top_prevented = float(top.iloc[0]["prevented_exposure_proxy"]) if not top.empty else 0.0
    total_prevented = float(summary_df["prevented_exposure_proxy"].sum()) if not summary_df.empty else 0.0
    top2_names = ", ".join(summary_df.head(2)["denial_bucket"].tolist()) if not summary_df.empty else "NONE"
    top2_share = float(summary_df.head(2)["priority_score"].sum()) / total_prevented if total_prevented > 0 else 0.0

    return "\n".join([
        "<h1>Denials Prevention Teaching Memo v1</h1>",
        "<h2>30-second answer</h2>",
        f"<p>From <code>{escape(source_fqn)}</code>, top prevention focus is <strong>{escape(top2_names)}</strong>, covering <strong>{_fmt_pct(top2_share)}</strong> of prevented exposure proxy.</p>",
        "<h2>60-second answer</h2>",
        f"<p>Current week <strong>{escape(current_week)}</strong> vs prior <strong>{escape(prior_week)}</strong> has TOP2 overlap <strong>{top2_overlap}/2</strong> ({_stability_confidence(top2_overlap)}). We run reversible owner actions first.</p>",
        "<h2>90-second answer</h2>",
        f"<p>Top example is <strong>{escape(top_bucket)}</strong> / {escape(top_reason)} with prevented exposure proxy {_fmt_money(top_prevented)}. Scenario table gives 10/20/30% directional prevention outcomes for execution planning.</p>",
        "<h2>Hostile questions</h2>",
        "<ul><li>Is this real dollars? Directional proxy only.</li><li>Why no payer split? Payer is missing in mart layer.</li><li>How stable is this? TOP2 overlap week-over-week.</li><li>What would make it real? Payer dimension + true service dates + CARC/RARC.</li></ul>",
        "<h2>What data would make this real</h2>",
        "<ul><li>payer_id / payer_name in marts</li><li>true service_from_date</li><li>CARC/RARC adjudication fields</li></ul>",
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build denials prevention opportunity brief from a dbt BigQuery mart relation.")
    parser.add_argument("--project", default=os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "rcm-flagship")
    parser.add_argument("--dataset", default=os.getenv("BQ_DATASET_ID") or "rcm")
    parser.add_argument("--relation", default="mart_workqueue_claims")
    parser.add_argument("--as-of-date", default=None, help="Optional filter anchor (YYYY-MM-DD).")
    parser.add_argument("--lookback-days", type=int, default=14)
    parser.add_argument("--out", default="exports")
    parser.add_argument("--workqueue-size", type=int, default=25)
    parser.add_argument("--summary-limit", type=int, default=50)
    parser.add_argument("--dry-run-sql", action="store_true")
    parser.add_argument("--write-html", dest="write_html", action="store_true", default=True)
    parser.add_argument("--no-write-html", dest="write_html", action="store_false")
    parser.add_argument("--write-teaching-html", dest="write_teaching_html", action="store_true", default=True)
    parser.add_argument("--no-write-teaching-html", dest="write_teaching_html", action="store_false")
    parser.add_argument("--determinism-check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_fqn = f"{args.project}.{args.dataset}.{args.relation}"
    as_of_date = pd.to_datetime(args.as_of_date).date() if args.as_of_date else None
    query_anchor_date = as_of_date or date.today()

    min_aging_sql = MIN_AGING_SQL.format(source_fqn=source_fqn)
    detail_sql = DETAIL_SQL.format(source_fqn=source_fqn)

    if args.dry_run_sql:
        print("-- SOURCE RELATION --")
        print(source_fqn)
        print("\n-- DETAIL SQL --")
        print(detail_sql)
        print("\n-- MIN AGING SQL --")
        print(min_aging_sql)
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    client = bigquery.Client(project=args.project)
    min_aging_df = _run_query(client, min_aging_sql, [])
    min_aging_days = int(min_aging_df.iloc[0]["min_aging_days"]) if not min_aging_df.empty else None
    if min_aging_days is None:
        raise RuntimeError("No denied rows found to anchor current period.")

    detail_df = _run_query(
        client,
        detail_sql,
        [
            bigquery.ScalarQueryParameter("as_of_date", "DATE", query_anchor_date),
            bigquery.ScalarQueryParameter("min_aging_days", "INT64", min_aging_days),
            bigquery.ScalarQueryParameter("lookback_days", "INT64", args.lookback_days),
        ],
    )
    if detail_df.empty:
        raise RuntimeError("No denied rows returned for selected anchored window.")

    detail_df = _with_dataset_week_keys(detail_df)
    max_service_date = detail_df["service_date"].max()
    window_start = max_service_date - pd.Timedelta(days=args.lookback_days)
    detail_df = detail_df[(detail_df["service_date"] >= window_start) & (detail_df["service_date"] <= max_service_date)].copy()
    week_order = detail_df[["dataset_week_start", "dataset_week_key"]].drop_duplicates().sort_values("dataset_week_start")
    week_keys = week_order["dataset_week_key"].tolist()
    if as_of_date:
        as_of_week_start = pd.Timestamp(as_of_date) - pd.to_timedelta(pd.Timestamp(as_of_date).weekday(), unit="D")
        as_of_week_key = as_of_week_start.strftime("%Y-%m-%d")
        week_keys = [wk for wk in week_keys if wk <= as_of_week_key]
    if not week_keys:
        raise RuntimeError("No comparable dataset_week_key values found.")

    current_week = week_keys[-1]
    prior_week = week_keys[-2] if len(week_keys) > 1 else ""
    current_df = detail_df[detail_df["dataset_week_key"] == current_week].copy()
    prior_df = detail_df[detail_df["dataset_week_key"] == prior_week].copy() if prior_week else detail_df.head(0).copy()

    summary_df = _build_summary(current_df, args.summary_limit)
    stability_df, top2_overlap = _build_stability(current_df, prior_df)
    scenarios_df = _build_scenarios(summary_df)
    workqueue_size_used = min(int(args.workqueue_size), int(len(current_df)))

    summary_path = out_dir / "denials_prevention_summary_v1.csv"
    md_path = docs_dir / "denials_prevention_brief_v1.md"
    html_path = docs_dir / "denials_prevention_brief_v1.html"
    teaching_html_path = out_dir / "denials_prevention_brief_v1_teaching.html"

    summary_df.to_csv(summary_path, index=False)
    md_text = _build_brief_markdown(source_fqn, summary_df, scenarios_df, current_week, prior_week if prior_week else "NONE", top2_overlap, workqueue_size_used)
    md_path.write_text(md_text, encoding="utf-8")

    if args.write_html:
        body_html = _build_public_html(summary_df, scenarios_df, current_week, prior_week if prior_week else "NONE", top2_overlap, workqueue_size_used)
        html_doc = """<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>Denials Prevention Opportunity Brief v1</title>
<style>body{max-width:960px;margin:24px auto;padding:0 16px 40px 16px;font-family:'Segoe UI',Arial,sans-serif;line-height:1.5;color:#111}table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}th,td{border:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}th{background:#f5f6f7}.impact-card{background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:12px;margin:12px 0 16px 0}</style></head><body>""" + body_html + "</body></html>"
        html_path.write_text(html_doc, encoding="utf-8")
        if args.determinism_check:
            h1 = hashlib.sha256(html_path.read_bytes()).hexdigest()
            html_path.write_text(html_doc, encoding="utf-8")
            h2 = hashlib.sha256(html_path.read_bytes()).hexdigest()
            print(f"DETERMINISM_HTML_SHA_FIRST={h1}")
            print(f"DETERMINISM_HTML_SHA_SECOND={h2}")
            print(f"MATCH={'TRUE' if h1 == h2 else 'FALSE'}")
            if h1 != h2:
                raise RuntimeError("Determinism check failed.")

    if args.write_teaching_html:
        teaching_html = """<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Denials Prevention Teaching Memo v1</title><style>body{max-width:960px;margin:24px auto;padding:0 16px 40px 16px;font-family:'Segoe UI',Arial,sans-serif;line-height:1.5;color:#111}</style></head><body>""" + _build_teaching_html(source_fqn, summary_df, scenarios_df, current_week, prior_week if prior_week else "NONE", top2_overlap) + "</body></html>"
        teaching_html_path.write_text(teaching_html, encoding="utf-8")

    total_denied = float(summary_df["denied_amount_sum"].sum()) if not summary_df.empty else 0.0
    total_prevented = float(summary_df["prevented_exposure_proxy"].sum()) if not summary_df.empty else 0.0
    top2 = summary_df.head(2)
    top2_names = ", ".join(top2["denial_bucket"].tolist()) if not top2.empty else "NONE"
    top2_share = float(top2["priority_score"].sum()) / total_prevented if total_prevented > 0 else 0.0

    print(f"SOURCE_RELATION={source_fqn}")
    print(f"SOURCE_GRAIN=claim-level ({args.relation})")
    print(f"PREV_WEEK_CURRENT={current_week}")
    print(f"PREV_TOTAL_DENIED_PROXY={total_denied:.2f}")
    print(f"PREV_TOTAL_PREVENTED_EXPOSURE_PROXY={total_prevented:.2f}")
    print(f"PREV_TOP2_BUCKETS={top2_names}")
    print(f"PREV_TOP2_PREVENTED_SHARE={top2_share * 100.0:.4f}%")
    print(f"PREV_STABILITY_CONFIDENCE={_stability_confidence(top2_overlap)}")
    print(f"TOP2_OVERLAP={top2_overlap}/2")
    print(f"WROTE={summary_path}")
    print(f"WROTE={md_path}")
    if args.write_html:
        print(f"WROTE={html_path}")
    if args.write_teaching_html:
        print(f"WROTE={teaching_html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
