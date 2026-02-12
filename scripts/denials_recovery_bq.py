from __future__ import annotations

import argparse
import hashlib
import re
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd
from google.cloud import bigquery


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


DETAIL_SQL = """
WITH base AS (
  SELECT
    CAST(clm_id AS STRING) AS claim_id,
    DATE_SUB(@anchor_date, INTERVAL CAST(COALESCE(aging_days, 0) AS INT64) DAY) AS service_date,
    DATE_TRUNC(
      DATE_SUB(@anchor_date, INTERVAL CAST(COALESCE(aging_days, 0) AS INT64) DAY),
      WEEK(MONDAY)
    ) AS dataset_week_key,
    CAST(COALESCE(aging_days, 0) AS INT64) AS aging_days,
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
    COALESCE(top_denial_group, '') AS top_denial_group,
    COALESCE(top_denial_prcsg, '') AS top_denial_prcsg,
    COALESCE(top_next_best_action, '') AS top_next_best_action,
    COALESCE(denied_potential_allowed_proxy_amt, 0.0) AS denied_amount_proxy,
    COALESCE(p_denial, 0.0) AS p_denial
  FROM `{source_fqn}`
  WHERE CAST(COALESCE(aging_days, 0) AS INT64) BETWEEN @min_aging_days AND (@min_aging_days + @lookback_days)
),
denied AS (
  SELECT
    *,
    (
      p_denial > 0
      OR top_denial_prcsg != ''
      OR top_denial_group != ''
      OR denied_amount_proxy > 0
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
scored AS (
  SELECT
    *,
    CASE
      WHEN denial_bucket IN ('AUTH_ELIG', 'CODING_DOC', 'TIMELY_FILING', 'DUPLICATE') THEN 1.0
      WHEN denial_bucket = 'CONTRACTUAL' THEN 0.2
      ELSE 0.6
    END AS recoverability_weight,
    CASE
      WHEN aging_days <= 30 THEN 1.0
      WHEN aging_days <= 60 THEN 0.9
      WHEN aging_days <= 90 THEN 0.75
      ELSE 0.5
    END AS time_weight
  FROM bucketed
)
SELECT
  claim_id,
  service_date,
  dataset_week_key,
  aging_days,
  denial_reason_raw AS denial_reason,
  denial_bucket,
  denied_amount_proxy,
  recoverability_weight,
  time_weight,
  denied_amount_proxy * recoverability_weight * time_weight AS recovery_priority_score
FROM scored
ORDER BY dataset_week_key DESC, recovery_priority_score DESC, claim_id
"""


OWNER_MAP = {
    "AUTH_ELIG": "Eligibility/Auth team",
    "CODING_DOC": "Coding/CDI",
    "TIMELY_FILING": "Billing",
    "DUPLICATE": "Billing",
    "CONTRACTUAL": "Contracting/RCM lead",
    "OTHER_PROXY": "RCM analyst review",
}


NEXT_ACTION_MAP = {
    "AUTH_ELIG": "Verify eligibility/auth; obtain auth; rebill",
    "CODING_DOC": "Coding review; validate modifiers/diagnoses; resubmit",
    "TIMELY_FILING": "Validate filing date; appeal if eligible; write-off if expired",
    "DUPLICATE": "Confirm duplicate; adjust/void as needed",
    "CONTRACTUAL": "Confirm contract terms; route non-recoverable to write-off policy",
    "OTHER_PROXY": "Manual triage; classify reason; assign owner",
}


EVIDENCE_MAP = {
    "AUTH_ELIG": "Auth # and eligibility response",
    "CODING_DOC": "Coding notes and supporting documentation",
    "TIMELY_FILING": "Filing limit and submission timestamps",
    "DUPLICATE": "Claim history and matching identifiers",
    "CONTRACTUAL": "Contract excerpt and allowed schedule",
    "OTHER_PROXY": "Manual triage notes and reason evidence",
}


def _fmt_money(value: float) -> str:
    return f"${value:,.0f}"


def _fmt_pct(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def _render_inline_no_links(text: str) -> str:
    rendered = escape(text)
    return re.sub(r"`([^`]+)`", lambda m: f"<code>{escape(m.group(1))}</code>", rendered)


def _render_inline(text: str) -> str:
    parts: list[str] = []
    last = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        before = text[last:match.start()]
        if before:
            parts.append(_render_inline_no_links(before))
        label = _render_inline_no_links(match.group(1))
        href = escape(match.group(2), quote=True)
        parts.append(f'<a href="{href}">{label}</a>')
        last = match.end()
    tail = text[last:]
    if tail:
        parts.append(_render_inline_no_links(tail))
    if not parts:
        return _render_inline_no_links(text)
    return "".join(parts)


def _split_pipe_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def _is_pipe_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and "|" in stripped[1:-1]


def _is_pipe_separator(line: str) -> bool:
    cells = _split_pipe_row(line)
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    out: list[str] = []
    i = 0
    in_code = False
    code_lines: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(part.strip() for part in paragraph_lines if part.strip())
            if text:
                out.append(f"<p>{_render_inline(text)}</p>")
            paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            out.append("<ul>")
            for item in list_items:
                out.append(f"<li>{_render_inline(item)}</li>")
            out.append("</ul>")
            list_items = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                out.append("<pre><code>")
                out.append(escape("\n".join(code_lines)))
                out.append("</code></pre>")
                code_lines = []
                in_code = False
            else:
                code_lines.append(line)
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            in_code = True
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            i += 1
            continue

        if _is_pipe_row(line) and (i + 1) < len(lines) and _is_pipe_separator(lines[i + 1]):
            flush_paragraph()
            flush_list()
            header = _split_pipe_row(line)
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and _is_pipe_row(lines[i]):
                rows.append(_split_pipe_row(lines[i]))
                i += 1
            out.append("<table>")
            out.append("<thead><tr>" + "".join(f"<th>{_render_inline(cell)}</th>" for cell in header) + "</tr></thead>")
            out.append("<tbody>")
            for row in rows:
                out.append("<tr>" + "".join(f"<td>{_render_inline(cell)}</td>" for cell in row) + "</tr>")
            out.append("</tbody></table>")
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_render_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:].strip())
            i += 1
            continue

        paragraph_lines.append(line)
        i += 1

    flush_paragraph()
    flush_list()
    return "\n".join(out)


def _stacked_bar_html(shares: list[tuple[str, float]]) -> str:
    segments = []
    labels = []
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b", "#17becf"]
    for idx, (label, share) in enumerate(shares):
        pct = max(0.0, share * 100.0)
        color = palette[idx % len(palette)]
        segments.append(
            f'<span style="width:{pct:.2f}%;background:{color};display:block;height:100%;"></span>'
        )
        labels.append(
            f'<span style="margin-right:12px;"><span style="display:inline-block;width:10px;height:10px;background:{color};margin-right:4px;"></span>{escape(label)} ({pct:.1f}%)</span>'
        )
    return (
        '<h2>Exposure concentration</h2>'
        '<div class="stacked-bar">' + "".join(segments) + "</div>"
        '<div class="stacked-bar-legend">' + "".join(labels) + "</div>"
    )


def _to_html_document(title: str, markdown_text: str, shares: list[tuple[str, float]]) -> str:
    body_html = _markdown_to_html(markdown_text)
    stacked_html = _stacked_bar_html(shares)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{
      max-width: 980px;
      margin: 24px auto;
      padding: 0 16px 40px 16px;
      font-family: "Segoe UI", Arial, sans-serif;
      line-height: 1.5;
      color: #111;
    }}
    h1, h2, h3 {{ margin-top: 1.2em; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0 18px 0;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid #d0d7de;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: #f6f8fa; }}
    code {{
      background: #f6f8fa;
      border: 1px solid #d0d7de;
      border-radius: 4px;
      padding: 0 4px;
      font-size: 90%;
    }}
    .stacked-bar {{
      display: flex;
      width: 100%;
      height: 24px;
      border: 1px solid #d0d7de;
      border-radius: 4px;
      overflow: hidden;
      margin: 8px 0 10px 0;
    }}
    .stacked-bar-legend {{
      font-size: 13px;
      margin-bottom: 16px;
    }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  {stacked_html}
  {body_html}
</body>
</html>
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dataset_week_from_value(value: object) -> str:
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def _build_brief_markdown(
    source_fqn: str,
    anchor_mode: str,
    current_week_key: str,
    prior_week_key: str,
    summary_df: pd.DataFrame,
    workqueue_df: pd.DataFrame,
    aging_df: pd.DataFrame,
    stability_df: pd.DataFrame,
    top2_overlap: int,
) -> str:
    total_priority = float(summary_df["priority_score"].sum()) if not summary_df.empty else 0.0
    top2 = summary_df.head(2).copy()
    top2_share = float(top2["priority_score"].sum() / total_priority) if total_priority > 0 else 0.0

    decision = "Focus this week on top 2 denial buckets by recovery priority score."
    status = "LIMITED_CONTEXT"
    reason = (
        "Ranking is directional and proxy-based; payer identity, true service dates, and CARC/RARC are not available in this mart layer."
    )

    lines: list[str] = [
        "# Denials Recovery Opportunity Brief v1",
        "",
        f"- **Source relation:** `{source_fqn}` (dbt mart only)",
        f"- **Anchoring:** `{anchor_mode}` | current `{current_week_key}` | prior `{prior_week_key}`",
        "",
        "## Decision",
        f"- {decision}",
        f"- Top 2 buckets represent **{_fmt_pct(top2_share)}** of current weighted exposure.",
        "",
        "## Status + Reason",
        f"- **Status:** {status}",
        f"- **Reason:** {reason}",
        "",
        "## Recovery focus this week (top drivers)",
    ]

    for _, row in summary_df.head(5).iterrows():
        lines.append(
            "- "
            + f"{row['denial_bucket']} / {row['denial_reason']}: "
            + f"{_fmt_money(float(row['denied_amount_sum']))} "
            + f"weighted {_fmt_money(float(row['priority_score']))} "
            + f"({int(row['denial_count'])} claims)"
        )

    lines.extend(
        [
            "",
            "## Aging bands",
            "| aging_band | denial_count | denied_amount_sum | priority_score_sum | priority_share |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in aging_df.iterrows():
        lines.append(
            f"| {row['aging_band']} | {int(row['denial_count'])} | {_fmt_money(float(row['denied_amount_sum']))} | "
            + f"{_fmt_money(float(row['priority_score_sum']))} | {_fmt_pct(float(row['priority_share']))} |"
        )

    lines.extend(
        [
            "",
            "## Stability (Current vs Prior)",
            f"- Top2 overlap: **{top2_overlap}/2** buckets",
            "| denial_bucket | current_rank | prior_rank | rank_delta | current_share | prior_share | share_delta | delta_priority_score |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in stability_df.iterrows():
        lines.append(
            f"| {row['denial_bucket']} | {int(row['current_rank'])} | {int(row['prior_rank'])} | {int(row['rank_delta'])} | "
            + f"{_fmt_pct(float(row['current_share']))} | {_fmt_pct(float(row['prior_share']))} | "
            + f"{_fmt_pct(float(row['share_delta']))} | {_fmt_money(float(row['delta_priority_score']))} |"
        )

    lines.extend(
        [
            "",
            "## Workqueue routing",
            f"- Workqueue size: **{len(workqueue_df)}** claims",
            "- Owners are bucket-mapped and include required evidence fields for first-touch.",
            "",
            "## Falsification",
            "- If next dataset week materially changes top-bucket ranks/shares, re-prioritize before scaling actions.",
            "",
            "## Data gaps and proxy caveats",
            "- `payer_dim_status='MISSING_IN_MART'` because payer identity is unavailable in current marts.",
            "- `service_date` is proxy-derived from `aging_days`.",
            "- `denied_amount` uses `denied_potential_allowed_proxy_amt` (proxy).",
            "",
            "## Field mapping (proxy-aware)",
            "| Output field | Source field | Notes |",
            "|---|---|---|",
            "| claim_id | `clm_id` | claim-grain identifier |",
            "| denied_amount | `denied_potential_allowed_proxy_amt` | proxy for denied amount |",
            "| denial_reason | `top_denial_group` / `top_denial_prcsg` | best available reason text |",
            "| service_date | derived from `aging_days` | proxy date for dataset-week anchoring |",
            "| payer_dim_status | constant `MISSING_IN_MART` | payer identity is unavailable |",
            "",
            "## Generated outputs",
            "- Summary CSV: `exports/denials_recovery_summary_v1.csv`",
            "- Workqueue CSV: `exports/denials_recovery_workqueue_v1.csv`",
            "- Aging bands CSV: `exports/denials_recovery_aging_bands_v1.csv`",
            "- Stability CSV: `exports/denials_recovery_stability_v1.csv`",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def _build_aging_bands(df_current: pd.DataFrame) -> pd.DataFrame:
    if df_current.empty:
        return pd.DataFrame(
            columns=["aging_band", "denial_count", "denied_amount_sum", "priority_score_sum", "priority_share"]
        )
    bands = pd.cut(
        df_current["aging_days"],
        bins=[-1, 30, 60, 90, 10_000],
        labels=["<=30", "31-60", "61-90", ">90"],
    )
    grouped = (
        df_current.assign(aging_band=bands)
        .groupby("aging_band", observed=True, as_index=False)
        .agg(
            denial_count=("claim_id", "size"),
            denied_amount_sum=("denied_amount_proxy", "sum"),
            priority_score_sum=("recovery_priority_score", "sum"),
        )
    )
    total = float(grouped["priority_score_sum"].sum())
    grouped["priority_share"] = grouped["priority_score_sum"] / total if total > 0 else 0.0
    order = {"<=30": 0, "31-60": 1, "61-90": 2, ">90": 3}
    grouped["order"] = grouped["aging_band"].astype(str).map(order).fillna(99)
    grouped = grouped.sort_values(["order", "aging_band"]).drop(columns=["order"]).reset_index(drop=True)
    return grouped


def _compute_stability(current_df: pd.DataFrame, prior_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    current = current_df.groupby("denial_bucket", as_index=False).agg(current_priority_score=("recovery_priority_score", "sum"))
    prior = prior_df.groupby("denial_bucket", as_index=False).agg(prior_priority_score=("recovery_priority_score", "sum"))
    merged = current.merge(prior, on="denial_bucket", how="outer").fillna(0.0)

    current_total = float(merged["current_priority_score"].sum())
    prior_total = float(merged["prior_priority_score"].sum())
    merged["current_share"] = merged["current_priority_score"] / current_total if current_total > 0 else 0.0
    merged["prior_share"] = merged["prior_priority_score"] / prior_total if prior_total > 0 else 0.0
    merged["share_delta"] = merged["current_share"] - merged["prior_share"]
    merged["delta_priority_score"] = merged["current_priority_score"] - merged["prior_priority_score"]

    merged = merged.sort_values(["current_priority_score", "prior_priority_score", "denial_bucket"], ascending=[False, False, True]).reset_index(drop=True)
    merged["current_rank"] = merged["current_priority_score"].rank(method="dense", ascending=False).astype(int)
    merged["prior_rank"] = merged["prior_priority_score"].rank(method="dense", ascending=False).astype(int)
    merged["rank_delta"] = merged["prior_rank"] - merged["current_rank"]

    current_top2 = set(merged.sort_values(["current_priority_score", "denial_bucket"], ascending=[False, True]).head(2)["denial_bucket"])
    prior_top2 = set(merged.sort_values(["prior_priority_score", "denial_bucket"], ascending=[False, True]).head(2)["denial_bucket"])
    top2_overlap = len(current_top2.intersection(prior_top2))

    ordered = merged[
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
    ].sort_values(["current_rank", "denial_bucket"], ascending=[True, True]).reset_index(drop=True)
    return ordered, top2_overlap


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate denials recovery brief outputs from BigQuery dbt mart.")
    parser.add_argument("--project", default="rcm-flagship")
    parser.add_argument("--dataset", default="rcm")
    parser.add_argument("--relation", default="mart_workqueue_claims")
    parser.add_argument("--out", default="exports")
    parser.add_argument("--workqueue-size", type=int, default=25)
    parser.add_argument("--summary-limit", type=int, default=50)
    parser.add_argument("--lookback-days", type=int, default=14)
    parser.add_argument("--as-of-date", type=str, default="", help="Optional anchor date (YYYY-MM-DD) filter.")
    parser.add_argument("--dry-run-sql", action="store_true", help="Print SQL statements only; do not execute.")
    parser.add_argument("--write-html", dest="write_html", action="store_true")
    parser.add_argument("--no-write-html", dest="write_html", action="store_false")
    parser.add_argument("--determinism-check", action="store_true", help="Write public HTML twice and compare SHA256.")
    parser.set_defaults(write_html=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    source_fqn = f"{args.project}.{args.dataset}.{args.relation}"
    anchor_date = date.fromisoformat(args.as_of_date) if args.as_of_date else date.today()

    if args.dry_run_sql:
        print(f"SOURCE={source_fqn}")
        print("\n-- MIN_AGING_SQL --")
        print(MIN_AGING_SQL.format(source_fqn=source_fqn))
        print("\n-- DETAIL_SQL --")
        print(DETAIL_SQL.format(source_fqn=source_fqn))
        return 0

    client = bigquery.Client(project=args.project)

    min_aging_query = MIN_AGING_SQL.format(source_fqn=source_fqn)
    min_df = client.query(min_aging_query).result().to_dataframe()
    min_aging_days = int(min_df.iloc[0]["min_aging_days"]) if not min_df.empty and pd.notna(min_df.iloc[0]["min_aging_days"]) else 0

    detail_query = DETAIL_SQL.format(source_fqn=source_fqn)
    params = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("anchor_date", "DATE", anchor_date.isoformat()),
            bigquery.ScalarQueryParameter("min_aging_days", "INT64", min_aging_days),
            bigquery.ScalarQueryParameter("lookback_days", "INT64", args.lookback_days),
        ]
    )
    detail_df = client.query(detail_query, job_config=params).result().to_dataframe()
    if detail_df.empty:
        raise RuntimeError("No denied rows found for the configured window.")

    detail_df["dataset_week_key"] = pd.to_datetime(detail_df["dataset_week_key"]).dt.date
    detail_df["service_date"] = pd.to_datetime(detail_df["service_date"]).dt.date

    week_keys = sorted(detail_df["dataset_week_key"].unique())
    current_dataset_week_key = week_keys[-1]
    prior_dataset_week_key = week_keys[-2] if len(week_keys) > 1 else None
    anchor_mode = "AS_OF_DATE_FILTERED" if args.as_of_date else "DATASET_MAX_WEEK"

    current_df = detail_df[detail_df["dataset_week_key"] == current_dataset_week_key].copy()
    prior_df = (
        detail_df[detail_df["dataset_week_key"] == prior_dataset_week_key].copy()
        if prior_dataset_week_key is not None
        else detail_df.iloc[0:0].copy()
    )

    summary_df = (
        current_df.groupby(["denial_bucket", "denial_reason"], as_index=False)
        .agg(
            denied_amount_sum=("denied_amount_proxy", "sum"),
            denial_count=("claim_id", "size"),
            avg_denied_amount=("denied_amount_proxy", "mean"),
            recoverability_weight=("recoverability_weight", "max"),
            priority_score=("recovery_priority_score", "sum"),
        )
        .sort_values(["priority_score", "denied_amount_sum", "denial_bucket", "denial_reason"], ascending=[False, False, True, True])
        .head(args.summary_limit)
        .reset_index(drop=True)
    )
    summary_df["payer_dim_status"] = "MISSING_IN_MART"
    summary_out = summary_df[
        [
            "denial_bucket",
            "denial_reason",
            "denied_amount_sum",
            "denial_count",
            "avg_denied_amount",
            "recoverability_weight",
            "priority_score",
            "payer_dim_status",
        ]
    ]

    workqueue_df = (
        current_df.sort_values(
            ["recovery_priority_score", "denied_amount_proxy", "claim_id"],
            ascending=[False, False, True],
        )
        .head(args.workqueue_size)
        .copy()
    )
    workqueue_df["owner"] = workqueue_df["denial_bucket"].map(OWNER_MAP).fillna("RCM analyst review")
    workqueue_df["next_action"] = workqueue_df["denial_bucket"].map(NEXT_ACTION_MAP).fillna("Manual triage")
    workqueue_df["evidence_needed"] = workqueue_df["denial_bucket"].map(EVIDENCE_MAP).fillna("Manual evidence collection")
    workqueue_df["payer_dim_status"] = "MISSING_IN_MART"
    workqueue_df["dataset_week_key"] = workqueue_df["dataset_week_key"].astype(str)
    workqueue_df["service_date"] = workqueue_df["service_date"].astype(str)
    workqueue_df = workqueue_df.rename(
        columns={
            "denied_amount_proxy": "denied_amount",
        }
    )
    workqueue_out = workqueue_df[
        [
            "claim_id",
            "dataset_week_key",
            "service_date",
            "denial_reason",
            "denial_bucket",
            "aging_days",
            "denied_amount",
            "recoverability_weight",
            "time_weight",
            "recovery_priority_score",
            "owner",
            "next_action",
            "evidence_needed",
            "payer_dim_status",
        ]
    ]

    aging_df = _build_aging_bands(current_df)
    stability_df, top2_overlap = _compute_stability(current_df, prior_df)

    out_dir = Path(args.out)
    docs_dir = Path("docs")
    summary_path = out_dir / "denials_recovery_summary_v1.csv"
    workqueue_path = out_dir / "denials_recovery_workqueue_v1.csv"
    aging_path = out_dir / "denials_recovery_aging_bands_v1.csv"
    stability_path = out_dir / "denials_recovery_stability_v1.csv"

    _write_csv(summary_out, summary_path)
    _write_csv(workqueue_out, workqueue_path)
    _write_csv(aging_df, aging_path)
    _write_csv(stability_df, stability_path)

    current_key_str = _dataset_week_from_value(current_dataset_week_key)
    prior_key_str = _dataset_week_from_value(prior_dataset_week_key) if prior_dataset_week_key else "NONE"
    markdown = _build_brief_markdown(
        source_fqn=source_fqn,
        anchor_mode=anchor_mode,
        current_week_key=current_key_str,
        prior_week_key=prior_key_str,
        summary_df=summary_out,
        workqueue_df=workqueue_out,
        aging_df=aging_df,
        stability_df=stability_df,
        top2_overlap=top2_overlap,
    )

    shares_df = (
        summary_out.groupby("denial_bucket", as_index=False)["priority_score"].sum().sort_values(["priority_score", "denial_bucket"], ascending=[False, True])
    )
    total_share = float(shares_df["priority_score"].sum())
    shares: list[tuple[str, float]] = []
    for _, row in shares_df.head(4).iterrows():
        share = float(row["priority_score"]) / total_share if total_share > 0 else 0.0
        shares.append((str(row["denial_bucket"]), share))
    shown_share = sum(share for _, share in shares)
    if shown_share < 0.999:
        shares.append(("Other", max(0.0, 1.0 - shown_share)))

    brief_md_path = docs_dir / "denials_recovery_brief_v1.md"
    brief_html_path = docs_dir / "denials_recovery_brief_v1.html"
    brief_md_path.write_text(markdown, encoding="utf-8")

    if args.write_html:
        html_text = _to_html_document("Denials Recovery Opportunity Brief v1", markdown, shares)
        brief_html_path.write_text(html_text, encoding="utf-8")
        if args.determinism_check:
            first_hash = _sha256(brief_html_path)
            brief_html_path.write_text(_to_html_document("Denials Recovery Opportunity Brief v1", markdown, shares), encoding="utf-8")
            second_hash = _sha256(brief_html_path)
            match = first_hash == second_hash
            print(f"DETERMINISM_HTML_SHA_FIRST={first_hash}")
            print(f"DETERMINISM_HTML_SHA_SECOND={second_hash}")
            print(f"MATCH={str(match).upper()}")
            if not match:
                raise RuntimeError("Determinism check failed: HTML SHA mismatch.")

    print(f"SOURCE={source_fqn}")
    print(f"ANCHOR_MODE={anchor_mode}")
    print(f"CURRENT_DATASET_WEEK_KEY={current_key_str}")
    print(f"PRIOR_DATASET_WEEK_KEY={prior_key_str}")
    print(f"TOP2_OVERLAP={top2_overlap}/2")
    print(f"WROTE={summary_path}")
    print(f"WROTE={workqueue_path}")
    print(f"WROTE={aging_path}")
    print(f"WROTE={stability_path}")
    print(f"WROTE={brief_md_path}")
    if args.write_html:
        print(f"WROTE={brief_html_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

