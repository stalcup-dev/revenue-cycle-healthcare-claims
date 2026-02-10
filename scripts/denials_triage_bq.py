from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any
from html import escape
from datetime import date

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
    COALESCE(top_denial_group, 'UNSPECIFIED') AS facility_or_service_line,
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
  denied_amount * preventability_weight AS row_priority
FROM weighted
ORDER BY service_date DESC, row_priority DESC
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


def _fmt_money(value: float) -> str:
    return f"${value:,.0f}"


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

        match = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if match:
            flush_paragraph()
            flush_list()
            level = len(match.group(1))
            out.append(f"<h{level}>{_render_inline(match.group(2))}</h{level}>")
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


def _to_html_document(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{
      max-width: 960px;
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
    pre {{
      background: #f6f8fa;
      border: 1px solid #d0d7de;
      border-radius: 6px;
      padding: 10px;
      overflow-x: auto;
    }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin: 12px 0 18px 0;
    }}
    .kpi {{
      border: 1px solid #d0d7de;
      border-radius: 8px;
      background: #f8fafc;
      padding: 10px 12px;
    }}
    .kpi-label {{
      font-size: 12px;
      color: #57606a;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      margin-bottom: 2px;
    }}
    .kpi-value {{
      font-size: 22px;
      font-weight: 600;
      line-height: 1.2;
    }}
    .priority-bars {{
      margin: 10px 0 16px 0;
    }}
    .priority-row {{
      margin: 8px 0;
    }}
    .priority-label {{
      font-size: 13px;
      margin-bottom: 2px;
      color: #24292f;
    }}
    .priority-track {{
      width: 100%;
      height: 14px;
      border-radius: 999px;
      background: #eaeef2;
      border: 1px solid #d0d7de;
      overflow: hidden;
    }}
    .priority-fill {{
      height: 100%;
      background: #0969da;
    }}
  </style>
</head>
<body>
{body_html}
</body>
</html>
"""


def _column_mapping_md() -> str:
    return "\n".join(
        [
            "| Conceptual field | Source column used | Notes |",
            "|---|---|---|",
            "| claim_id | `clm_id` | direct claim identifier |",
            "| payer_dim_status | constant `MISSING_IN_MART` | payer identity is unavailable in selected marts |",
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
        "Payer identity is unavailable in marts; denial reason and denied dollar values are proxy-derived for directional triage."
    )

    top5_lines: list[str] = []
    for _, row in top5.iterrows():
        top5_lines.append(
            f"- `{row['denial_bucket']}` / `{row['denial_reason']}`: "
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
        "## Data Gaps / Next Data Needed",
        "- Missing payer identity dimension (plan/carrier): not present in current marts.",
        "- `service_date` is estimated from `aging_days` (proxy).",
        "- `denied_amount` uses `denied_potential_allowed_proxy_amt` (proxy).",
        "- Needed in marts: `payer_id` / `payer_name`, actual `service_from_date`, and actual denial codes (`CARC`/`RARC`) if available.",
        "",
        "## Column mapping (required conceptual fields)",
        _column_mapping_md(),
        "",
        "Note: This brief intentionally excludes payer-level conclusions because payer identity is missing in current marts.",
    ]
    return "\n".join(lines) + "\n"


def _teaching_markdown(
    source_fqn: str,
    summary_df: pd.DataFrame,
    workqueue_df: pd.DataFrame,
    workqueue_size: int,
) -> str:
    top_bucket = summary_df.iloc[0]["denial_bucket"] if not summary_df.empty else "N/A"
    top_reason = summary_df.iloc[0]["denial_reason"] if not summary_df.empty else "N/A"
    top_priority = float(summary_df.iloc[0]["priority_score"]) if not summary_df.empty else 0.0
    total_invalid = int(summary_df["denial_count"].sum()) if not summary_df.empty else 0
    queue_top_owner = (
        workqueue_df.groupby("owner", as_index=False).size().sort_values("size", ascending=False).iloc[0]["owner"]
        if not workqueue_df.empty
        else "N/A"
    )

    return "\n".join(
        [
            "# Denials Triage Teaching Memo v1 (Private)",
            "",
            "## What this is",
            "- This is a private coaching memo to explain the denials triage brief in interview or stakeholder settings.",
            "- It mirrors the production brief and translates the logic into plain-language talk tracks.",
            "",
            "## Data source and grain",
            f"- Source relation: `{source_fqn}` (dbt mart only).",
            "- Grain: claim-level rows from the workqueue mart.",
            "",
            "## How the triage score works",
            "- We map each denied claim into a denial bucket using deterministic keyword rules.",
            "- Priority formula: `priority_score = denied_amount_sum * preventability_weight`.",
            "- Higher score means more preventable dollars are concentrated in that bucket.",
            "",
            "## What is proxy vs real",
            "- Payer identity is missing in this mart (`payer_dim_status = MISSING_IN_MART`).",
            "- `service_date` is estimated from `aging_days` and is a proxy.",
            "- `denied_amount` uses `denied_potential_allowed_proxy_amt`, also a proxy.",
            "",
            "## How to use outputs",
            "- Executive readers consume `docs/denials_triage_brief_v1.md` or `.html` for decision framing.",
            f"- Analysts execute the top {workqueue_size} rows in `exports/denials_workqueue_v1.csv` with owner routing and evidence requirements.",
            "",
            "## 90-second talk track",
            "1. Problem: denied dollars are concentrated and need immediate triage without over-claiming precision.",
            "2. Method: dbt mart only, deterministic bucket rules, weighted priority scoring, top-N workqueue.",
            f"3. Decision: focus this week on top denial buckets led by `{top_bucket}` / `{top_reason}`.",
            "4. Action: route queue by owner and gather required evidence before irreversible policy changes.",
            "5. Falsification: if top buckets or weighted exposure move materially next cycle, re-prioritize.",
            "",
            "## Five likely interview questions",
            "1. Why no payer insights? Because payer identity is missing in the mart; we state that explicitly and avoid false precision.",
            "2. Why use proxy denied amount? It is the only available consistent denied-dollar signal in this mart.",
            "3. Why weighted scoring? It separates likely preventable work from contractual/non-recoverable buckets.",
            "4. How do you avoid overreaction? LIMITED_CONTEXT framing and reversible actions first.",
            "5. What would make this stronger? Add payer_id/payer_name, true service dates, and CARC/RARC to marts.",
            "",
            "## Demo steps (30 seconds)",
            "```bash",
            "python scripts/denials_triage_bq.py --out exports --workqueue-size 25",
            "```",
            "- Summary CSV: `exports/denials_triage_summary_v1.csv`",
            "- Workqueue CSV: `exports/denials_workqueue_v1.csv`",
            "- Public brief: `docs/denials_triage_brief_v1.md` + `docs/denials_triage_brief_v1.html`",
            "- Private teaching memo: `exports/denials_triage_brief_v1_teaching.html`",
            "",
            f"## Quick context stats\n- Total denied rows in summary: {total_invalid:,}\n- Top priority score: {_fmt_money(top_priority)}\n- Top queue owner: {queue_top_owner}",
        ]
    ) + "\n"


def _visual_summary_html(summary_df: pd.DataFrame, workqueue_size: int) -> str:
    top5 = summary_df.head(5).copy()
    total_priority = float(summary_df["priority_score"].sum()) if not summary_df.empty else 0.0
    top2_priority = float(summary_df.head(2)["priority_score"].sum()) if not summary_df.empty else 0.0
    top2_share = (top2_priority / total_priority * 100.0) if total_priority > 0 else 0.0
    max_priority = float(top5["priority_score"].max()) if not top5.empty else 0.0

    kpi_html = f"""
<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-label">Top 2 share of priority</div>
    <div class="kpi-value">{top2_share:.1f}%</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Total weighted exposure</div>
    <div class="kpi-value">{escape(_fmt_money(total_priority))}</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Workqueue size</div>
    <div class="kpi-value">{workqueue_size}</div>
  </div>
</div>
"""

    table_rows: list[str] = []
    bars: list[str] = []
    for idx, (_, row) in enumerate(top5.iterrows(), start=1):
        priority = float(row["priority_score"])
        denied_amount = float(row["denied_amount_sum"])
        denied_count = int(row["denial_count"])
        width_pct = (priority / max_priority * 100.0) if max_priority > 0 else 0.0
        label = f"{row['denial_bucket']} / {row['denial_reason']}"

        table_rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{escape(str(row['denial_bucket']))}</td>"
            f"<td>{escape(str(row['denial_reason']))}</td>"
            f"<td>{escape(_fmt_money(denied_amount))}</td>"
            f"<td>{denied_count:,}</td>"
            f"<td>{escape(_fmt_money(priority))}</td>"
            "</tr>"
        )
        bars.append(
            f"""
<div class="priority-row">
  <div class="priority-label">{escape(label)} ({escape(_fmt_money(priority))})</div>
  <div class="priority-track"><div class="priority-fill" style="width:{width_pct:.1f}%"></div></div>
</div>
"""
        )

    table_html = (
        "<h2>Top Drivers</h2>"
        "<table><thead><tr>"
        "<th>Rank</th><th>Bucket</th><th>Reason</th><th>Denied $</th><th>Count</th><th>Priority score</th>"
        "</tr></thead><tbody>"
        + "".join(table_rows)
        + "</tbody></table>"
    )
    bars_html = "<h3>Priority bars</h3><div class=\"priority-bars\">" + "".join(bars) + "</div>"
    return kpi_html + table_html + bars_html


OWNER_MAP = {
    "AUTH_ELIG": "Eligibility/Auth team",
    "CODING_DOC": "Coding/CDI",
    "TIMELY_FILING": "Billing",
    "DUPLICATE": "Billing",
    "CONTRACTUAL": "Contracting/RCM lead",
    "OTHER_PROXY": "RCM analyst review",
}

ACTION_MAP = {
    "AUTH_ELIG": "Verify eligibility/auth; obtain auth; rebill",
    "CODING_DOC": "Coding review; validate modifiers/diagnoses; resubmit",
    "TIMELY_FILING": "Validate filing date; appeal if eligible; write-off if expired",
    "DUPLICATE": "Confirm duplicate; adjust/void as needed",
    "CONTRACTUAL": "Confirm contract terms; route non-recoverable to write-off policy",
    "OTHER_PROXY": "Manual triage; classify reason; assign owner",
}

EVIDENCE_MAP = {
    "AUTH_ELIG": "Auth number, eligibility response",
    "CODING_DOC": "Coding notes, op note, medical record excerpt",
    "TIMELY_FILING": "Filing limit, submission timestamps",
    "DUPLICATE": "Claim history, matching identifiers",
    "CONTRACTUAL": "Contract excerpt, allowed schedule",
    "OTHER_PROXY": "Denial reason detail, line notes, routing owner",
}


def _with_dataset_week_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["service_date"] = pd.to_datetime(out["service_date"])
    out["dataset_week_start"] = out["service_date"] - pd.to_timedelta(out["service_date"].dt.weekday, unit="D")
    out["dataset_week_key"] = out["dataset_week_start"].dt.strftime("%Y-%m-%d")
    return out


def _build_summary(current_df: pd.DataFrame, summary_limit: int) -> pd.DataFrame:
    grouped = (
        current_df.groupby(["denial_bucket", "denial_reason"], as_index=False)
        .agg(
            denied_amount_sum=("denied_amount", "sum"),
            denial_count=("claim_id", "count"),
            avg_denied_amount=("denied_amount", "mean"),
            preventability_weight=("preventability_weight", "first"),
            priority_score=("row_priority", "sum"),
        )
        .sort_values(
            ["priority_score", "denied_amount_sum", "denial_bucket", "denial_reason"],
            ascending=[False, False, True, True],
            kind="mergesort",
        )
        .head(summary_limit)
    )
    grouped["payer_dim_status"] = "MISSING_IN_MART"
    return grouped[
        [
            "denial_bucket",
            "denial_reason",
            "denied_amount_sum",
            "denial_count",
            "avg_denied_amount",
            "preventability_weight",
            "priority_score",
            "payer_dim_status",
        ]
    ]


def _build_workqueue(current_df: pd.DataFrame, workqueue_size: int) -> pd.DataFrame:
    workqueue = (
        current_df.sort_values(
            ["row_priority", "denied_amount", "claim_id"],
            ascending=[False, False, True],
            kind="mergesort",
        )
        .head(workqueue_size)
        .copy()
    )
    workqueue["owner"] = workqueue["denial_bucket"].map(OWNER_MAP).fillna("RCM analyst review")
    workqueue["next_action"] = workqueue["denial_bucket"].map(ACTION_MAP).fillna("Manual triage; classify reason; assign owner")
    workqueue["evidence_needed"] = workqueue["denial_bucket"].map(EVIDENCE_MAP).fillna("Denial reason detail, line notes, routing owner")
    workqueue["payer_dim_status"] = "MISSING_IN_MART"
    return workqueue[
        [
            "claim_id",
            "service_date",
            "dataset_week_key",
            "denial_reason",
            "denial_bucket",
            "denied_amount",
            "preventability_weight",
            "row_priority",
            "owner",
            "next_action",
            "evidence_needed",
            "payer_dim_status",
        ]
    ]


def _build_stability(current_df: pd.DataFrame, prior_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    current = current_df.groupby("denial_bucket", as_index=False).agg(current_priority_score=("row_priority", "sum"))
    prior = prior_df.groupby("denial_bucket", as_index=False).agg(prior_priority_score=("row_priority", "sum"))

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

    current_top2 = set(
        merged[merged["current_priority_score"] > 0]
        .sort_values(["current_priority_score", "denial_bucket"], ascending=[False, True], kind="mergesort")
        .head(2)["denial_bucket"]
        .tolist()
    )
    prior_top2 = set(
        merged[merged["prior_priority_score"] > 0]
        .sort_values(["prior_priority_score", "denial_bucket"], ascending=[False, True], kind="mergesort")
        .head(2)["denial_bucket"]
        .tolist()
    )
    overlap = len(current_top2.intersection(prior_top2))
    overlap_text = f"TOP2_OVERLAP={overlap}/2"

    return (
        merged[
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
        ],
        overlap_text,
    )


def _run_query(client: bigquery.Client, sql: str, params: list[bigquery.ScalarQueryParameter]) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(sql, job_config=job_config).result().to_dataframe()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build denials triage summary + workqueue from a single dbt BigQuery relation.")
    parser.add_argument("--project", default=os.getenv("BQ_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "rcm-flagship")
    parser.add_argument("--dataset", default=os.getenv("BQ_DATASET_ID") or "rcm")
    parser.add_argument("--relation", default="mart_workqueue_claims")
    parser.add_argument(
        "--as-of-date",
        default=None,
        help="Optional filter anchor (YYYY-MM-DD). If provided, select dataset weeks <= this derived week key.",
    )
    parser.add_argument("--lookback-days", type=int, default=14, help="Window size (days) for selecting current/prior weeks from latest available service_date.")
    parser.add_argument("--out", default="exports")
    parser.add_argument("--workqueue-size", type=int, default=25)
    parser.add_argument("--summary-limit", type=int, default=50)
    parser.add_argument("--dry-run-sql", action="store_true", help="Print SQL statements only; do not execute.")
    parser.add_argument("--write-html", dest="write_html", action="store_true", default=True, help="Write docs HTML brief.")
    parser.add_argument("--no-write-html", dest="write_html", action="store_false", help="Skip docs HTML brief.")
    parser.add_argument(
        "--write-teaching-html",
        dest="write_teaching_html",
        action="store_true",
        default=True,
        help="Write private teaching HTML memo under exports/.",
    )
    parser.add_argument(
        "--no-write-teaching-html",
        dest="write_teaching_html",
        action="store_false",
        help="Skip private teaching HTML memo.",
    )
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
        print(f"\n-- ANCHOR_MODE --\n{'AS_OF_DATE_FILTERED' if as_of_date else 'DATASET_MAX_WEEK'}")
        print(f"\n-- QUERY_ANCHOR_DATE --\n{query_anchor_date}")
        if as_of_date:
            print(f"\n-- AS_OF_DATE_FILTER --\n{as_of_date}")
        print(f"\n-- LOOKBACK_DAYS --\n{args.lookback_days}")
        print("\n-- MIN AGING SQL --")
        print(min_aging_sql)
        print("\n-- DETAIL SQL --")
        print(detail_sql)
        print("\n-- OUTPUTS --")
        print("summary/workqueue/stability are derived in Python from DETAIL SQL result.")
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
        raise RuntimeError("No denied rows returned for the selected anchored window.")

    detail_df = _with_dataset_week_keys(detail_df)
    all_detail_df = detail_df.copy()
    max_service_date = detail_df["service_date"].max()
    window_start = max_service_date - pd.Timedelta(days=args.lookback_days)
    window_df = detail_df[(detail_df["service_date"] >= window_start) & (detail_df["service_date"] <= max_service_date)].copy()
    if window_df.empty:
        window_df = detail_df.copy()

    detail_df = window_df
    anchor_mode = "DATASET_MAX_WEEK"
    week_order = detail_df[["dataset_week_start", "dataset_week_key"]].drop_duplicates().sort_values("dataset_week_start")
    week_keys = week_order["dataset_week_key"].tolist()
    if as_of_date:
        as_of_week_start = pd.Timestamp(as_of_date) - pd.to_timedelta(pd.Timestamp(as_of_date).weekday(), unit="D")
        as_of_week_key = as_of_week_start.strftime("%Y-%m-%d")
        week_keys = [wk for wk in week_keys if wk <= as_of_week_key]
        anchor_mode = "AS_OF_DATE_FILTERED"

    if len(week_keys) < 2:
        all_week_order = (
            all_detail_df[["dataset_week_start", "dataset_week_key"]]
            .drop_duplicates()
            .sort_values("dataset_week_start")
        )
        all_week_keys = all_week_order["dataset_week_key"].tolist()
        if as_of_date:
            all_week_keys = [wk for wk in all_week_keys if wk <= as_of_week_key]
        week_keys = all_week_keys

    if not week_keys:
        raise RuntimeError("No comparable dataset_week_key values found.")

    current_dataset_week_key = week_keys[-1]
    prior_dataset_week_key = week_keys[-2] if len(week_keys) > 1 else ""

    current_df = detail_df[detail_df["dataset_week_key"] == current_dataset_week_key].copy()
    prior_df = (
        detail_df[detail_df["dataset_week_key"] == prior_dataset_week_key].copy()
        if prior_dataset_week_key
        else detail_df.head(0).copy()
    )

    summary_df = _build_summary(current_df, args.summary_limit)
    workqueue_df = _build_workqueue(current_df, args.workqueue_size)
    stability_df, top2_overlap = _build_stability(current_df, prior_df)

    summary_path = out_dir / "denials_triage_summary_v1.csv"
    workqueue_path = out_dir / "denials_workqueue_v1.csv"
    stability_path = out_dir / "denials_stability_v1.csv"
    brief_path = docs_dir / "denials_triage_brief_v1.md"
    brief_html_path = docs_dir / "denials_triage_brief_v1.html"
    teaching_html_path = out_dir / "denials_triage_brief_v1_teaching.html"

    summary_df.to_csv(summary_path, index=False)
    workqueue_df.to_csv(workqueue_path, index=False)
    stability_df.to_csv(stability_path, index=False)
    brief_markdown = _brief_markdown(source_fqn, summary_df, workqueue_df, args.workqueue_size)
    brief_path.write_text(brief_markdown, encoding="utf-8")

    if args.write_html:
        visuals_html = _visual_summary_html(summary_df, args.workqueue_size)
        body_html = visuals_html + _markdown_to_html(brief_markdown)
        brief_html_path.write_text(
            _to_html_document("Denials Triage Brief v1", body_html),
            encoding="utf-8",
        )

    if args.write_teaching_html:
        teaching_markdown = _teaching_markdown(source_fqn, summary_df, workqueue_df, args.workqueue_size)
        teaching_html_path.write_text(
            _to_html_document("Denials Triage Teaching Memo v1", _markdown_to_html(teaching_markdown)),
            encoding="utf-8",
        )

    print(f"SOURCE_RELATION={source_fqn}")
    print(f"SOURCE_GRAIN=claim-level ({args.relation})")
    print(f"MIN_AGING_DAYS={min_aging_days}")
    print(f"ANCHOR_MODE={anchor_mode}")
    print(f"QUERY_ANCHOR_DATE={query_anchor_date}")
    print(f"CURRENT_DATASET_WEEK_KEY={current_dataset_week_key}")
    print(f"PRIOR_DATASET_WEEK_KEY={prior_dataset_week_key if prior_dataset_week_key else 'NONE'}")
    print(top2_overlap)
    print(f"WROTE={summary_path}")
    print(f"WROTE={workqueue_path}")
    print(f"WROTE={stability_path}")
    print(f"WROTE={brief_path}")
    if args.write_html:
        print(f"WROTE={brief_html_path}")
    if args.write_teaching_html:
        print(f"WROTE={teaching_html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
