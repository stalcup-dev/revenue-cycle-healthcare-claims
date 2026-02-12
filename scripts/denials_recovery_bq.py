from __future__ import annotations

import argparse
import hashlib
import json
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


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


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


def _impact_confidence_label(top2_overlap: int, sample_n: int) -> str:
    if top2_overlap >= 2 and sample_n >= 30:
        return "HIGH"
    if top2_overlap >= 2 and sample_n < 30:
        return "MEDIUM"
    return "LOW"


def _impact_card_html(impact: dict[str, object]) -> str:
    current_week_key = str(impact["current_week_key"])
    prior_week_key = str(impact["prior_week_key"])
    total_denied = float(impact["current_total_denied_amount_sum"])
    top2_priority_share = float(impact["top2_priority_share_pct"])
    top2_overlap = int(impact["top2_overlap"])
    confidence = str(impact["confidence_signal"])
    workqueue_size = int(impact["workqueue_size_used"])
    top2_names = str(impact["top2_bucket_names"])
    expected_recovery_amt = float(impact["expected_recovery_amt"])
    sample_n = int(impact["outcomes_sample_n"])
    sample_quality = str(impact["sample_quality"])

    outcomes_line = ""
    if sample_quality != "NO_OUTCOMES_PROVIDED":
        outcomes_line = (
            f"<li>Expected recovery amount (directional): <strong>{_fmt_money(expected_recovery_amt)}</strong>; "
            f"sample n <strong>{sample_n}</strong> (<strong>{escape(sample_quality)}</strong>).</li>"
        )
    return (
        "<section class=\"impact-card\">"
        + "<h2>Impact in 90 Seconds</h2>"
        + f"<p>Current week <strong>{escape(current_week_key)}</strong> vs prior week <strong>{escape(prior_week_key)}</strong>:</p>"
        + f"<ul><li>Total directional denied exposure (proxy): <strong>{_fmt_money(total_denied)}</strong>.</li>"
        + f"<li>Top 2 buckets ({escape(top2_names)}) account for <strong>{top2_priority_share:.1f}%</strong> of weighted exposure.</li>"
        + f"<li>Working the top <strong>{workqueue_size}</strong> items concentrates effort on highest expected recovery value first.</li>"
        + f"<li>Stability signal: <strong>{top2_overlap}/2 overlap</strong> week-over-week (<strong>{escape(confidence)}</strong> confidence).</li>"
        + outcomes_line
        + "</ul>"
        + "<p><strong>Safe for:</strong></p><ul><li>Directional triage</li><li>Owner routing</li></ul>"
        + "<p><strong>Not safe for:</strong></p><ul><li>Payer-level operational change</li><li>Causal ROI claims</li></ul>"
        + "</section>"
    )


def _opportunity_capacity_html(
    opportunity_df: pd.DataFrame,
    capacity_summary: dict[str, float | str | bool],
) -> str:
    if opportunity_df.empty:
        return "<h2>Opportunity & Capacity</h2><p>No opportunity rows available.</p>"

    top_df = opportunity_df.sort_values(
        ["workqueue_denied_sum", "denial_bucket"], ascending=[False, True]
    ).head(5)
    total = float(top_df["workqueue_denied_sum"].sum())
    if total <= 0:
        total = 1.0

    bar_rows: list[str] = []
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b"]
    for idx, row in top_df.reset_index(drop=True).iterrows():
        amt = float(row["workqueue_denied_sum"])
        width = max(2.0, (amt / total) * 100.0)
        label = str(row["denial_bucket"])
        share = amt / total
        recovered_rate = row.get("recovered_rate", pd.NA)
        if pd.notna(recovered_rate):
            rr_txt = f" | recovered rate {_fmt_pct(float(recovered_rate))}"
        else:
            rr_txt = ""
        bar_rows.append(
            "<div class=\"opp-row\">"
            + f"<div class=\"opp-label\">{escape(label)} ({_fmt_pct(share)}){escape(rr_txt)}</div>"
            + f"<div class=\"opp-bar-wrap\"><div class=\"opp-bar\" style=\"width:{width:.2f}%;background:{palette[idx % len(palette)]};\"></div></div>"
            + "</div>"
        )

    hours = float(capacity_summary["weekly_touch_budget_minutes"]) / 60.0
    touches = float(capacity_summary["expected_touches"])
    has_outcomes = bool(capacity_summary["has_outcomes"])
    if has_outcomes:
        recovered = float(capacity_summary["expected_recovered_amt"])
        summary_line = (
            f"At {hours:.1f} hrs/week, expected recovered dollars is about {_fmt_money(recovered)} "
            "(directional)."
        )
    else:
        summary_line = (
            f"At {hours:.1f} hrs/week, capacity supports about {touches:.1f} touches/week. "
            "No outcomes file provided; recovery dollars are directional placeholders."
        )

    return (
        "<h2>Opportunity & Capacity</h2>"
        + "<p>Directional view from current workqueue exposure and available outcomes.</p>"
        + "<div class=\"opp-panel\">"
        + "".join(bar_rows)
        + "</div>"
        + f"<p><strong>{escape(summary_line)}</strong></p>"
    )


def _to_html_document(
    title: str,
    markdown_text: str,
    shares: list[tuple[str, float]],
    opportunity_df: pd.DataFrame,
    capacity_summary: dict[str, float | str | bool],
    impact: dict[str, object],
) -> str:
    body_html = _markdown_to_html(markdown_text)
    stacked_html = _stacked_bar_html(shares)
    opportunity_html = _opportunity_capacity_html(opportunity_df, capacity_summary)
    impact_html = _impact_card_html(impact)
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
    .opp-panel {{
      margin: 8px 0 12px 0;
    }}
    .opp-row {{
      margin-bottom: 10px;
    }}
    .opp-label {{
      font-size: 13px;
      margin-bottom: 2px;
    }}
    .opp-bar-wrap {{
      width: 100%;
      height: 14px;
      border: 1px solid #d0d7de;
      border-radius: 4px;
      overflow: hidden;
      background: #f6f8fa;
    }}
    .opp-bar {{
      height: 100%;
    }}
    .impact-card {{
      border: 1px solid #d0d7de;
      border-radius: 8px;
      padding: 12px 14px;
      margin: 10px 0 16px 0;
      background: #f8fbff;
    }}
    .impact-card ul {{
      margin-top: 6px;
    }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  {impact_html}
  {stacked_html}
  {opportunity_html}
  {body_html}
</body>
</html>
"""


def _build_teaching_html(
    source_fqn: str,
    anchor_mode: str,
    current_week_key: str,
    prior_week_key: str,
    summary_df: pd.DataFrame,
    outcomes_metrics: dict[str, float] | None,
    impact: dict[str, object],
) -> str:
    top_row = summary_df.iloc[0] if not summary_df.empty else None
    worked_example = (
        f"Top row: {top_row['denial_bucket']} / {top_row['denial_reason']} | "
        f"count={int(top_row['denial_count'])} | priority_score={_fmt_money(float(top_row['priority_score']))}"
        if top_row is not None
        else "No summary rows available in this run."
    )
    metrics_block = (
        f"<li>Matched claims: {int(outcomes_metrics['matched_claims'])}</li>"
        f"<li>Recovered sum: {_fmt_money(outcomes_metrics['recovery_realized_sum'])}</li>"
        f"<li>Top-bucket recovery rate: {_fmt_pct(outcomes_metrics['top_bucket_recovery_rate'])}</li>"
        if outcomes_metrics is not None
        else "<li>No outcomes file provided in this run.</li>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Denials Recovery Teaching Guide v1</title>
  <style>
    body {{ max-width: 980px; margin: 24px auto; padding: 0 16px 40px 16px; font-family: Segoe UI, Arial, sans-serif; line-height: 1.5; }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0 16px 0; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px; padding: 0 4px; }}
  </style>
</head>
<body>
  <h1>Denials Recovery Teaching Guide v1</h1>
  <h2>What this is safe for</h2>
  <ul>
    <li>Directional triage prioritization from dbt mart outputs.</li>
    <li>Weekly owner routing and evidence planning.</li>
    <li>Stability checks between current and prior dataset-week.</li>
  </ul>
  <h2>What this is NOT safe for</h2>
  <ul>
    <li>Payer-level interventions (payer identity is missing in selected marts).</li>
    <li>Guaranteed recovery forecasting from proxy amounts.</li>
    <li>Causal claims about denial root cause.</li>
  </ul>
  <h2>Decision tree</h2>
  <ul>
    <li>If top-2 overlap is stable, focus those buckets first.</li>
    <li>If overlap breaks, run reversible investigation before scaling.</li>
    <li>Re-check next dataset-week before irreversible action.</li>
  </ul>
  <h2>90-second talk track</h2>
  <ul>
    <li>Problem: limited capacity and noisy denial reason data.</li>
    <li>Method: bucket + weighted scoring + week-over-week stability.</li>
    <li>Decision: focus top buckets with explicit proxy guardrails.</li>
    <li>Action: route queue with owner/evidence requirements.</li>
    <li>Falsification: if rank/share stability changes, re-prioritize.</li>
  </ul>
  <h2>How to Explain This in an Interview</h2>
  <h3>30-second answer</h3>
  <p>We rank denials using a deterministic weighted score from dbt marts, then route the top queue by owner and evidence. Current focus is {escape(str(impact["top2_bucket_names"]))}, covering {float(impact["top2_priority_share_pct"]):.1f}% of weighted exposure.</p>
  <h3>60-second answer</h3>
  <p>For week {escape(str(impact["current_week_key"]))}, directional denied exposure is {_fmt_money(float(impact["current_total_denied_amount_sum"]))}. Top 2 buckets represent {float(impact["top2_priority_share_pct"]):.1f}% of weighted exposure, with stability {int(impact["top2_overlap"])}/2 ({escape(str(impact["confidence_signal"]))}).</p>
  <h3>90-second answer</h3>
  <p>We use this for directional triage, not causal or payer-level commitments. Workqueue size is {int(impact["workqueue_size_used"])}, expected recovery is {_fmt_money(float(impact["expected_recovery_amt"]))} (directional), and actions stay reversible until richer marts add payer identity and CARC/RARC.</p>
  <h2>Hostile questions</h2>
  <ol>
    <li>Why no payer insights? Because payer identity is absent in this mart layer.</li>
    <li>Is this true denied dollars? No, denied amount is proxy-derived.</li>
    <li>Can we claim ROI? Not yet; outcomes are directional unless adjudication-sourced.</li>
    <li>Why this week anchor? Uses dataset max week for deterministic comparisons.</li>
    <li>How do you reduce proxy risk? Add payer_id, CARC/RARC, true service dates in marts.</li>
  </ol>
  <h2>Selection bias and false positives</h2>
  <h3>Why false positives happen</h3>
  <ul>
    <li>Proxy denied amounts can rank claims that later resolve as non-recoverable.</li>
    <li>Short windows can over-represent one denial process phase.</li>
    <li>Manual outcomes entry can lag true adjudication timing.</li>
  </ul>
  <h3>How to reduce them</h3>
  <ul>
    <li>Collect outcomes weekly and recalibrate bucket weights every cycle.</li>
    <li>Add payer_id and CARC/RARC to reduce OTHER_PROXY routing noise.</li>
    <li>Track resolved-within-window by bucket and de-prioritize low-yield buckets.</li>
  </ul>
  <h2>How to size action</h2>
  <ul>
    <li>Start with weekly touch budget and default touch minutes.</li>
    <li>Estimate touches, then convert to directional resolutions using observed resolved rate.</li>
    <li>Translate to directional recovered dollars and treat as planning bounds, not guarantees.</li>
  </ul>
  <h2>Worked example</h2>
  <p>{escape(worked_example)}</p>
  <h2>Anchor context</h2>
  <ul>
    <li>ANCHOR_MODE: <code>{escape(anchor_mode)}</code></li>
    <li>CURRENT_DATASET_WEEK_KEY: <code>{escape(current_week_key)}</code></li>
    <li>PRIOR_DATASET_WEEK_KEY: <code>{escape(prior_week_key)}</code></li>
    <li>Note: dataset-week is a synthetic-week anchor, not calendar operations week.</li>
  </ul>
  <h2>Proxy risk table</h2>
  <table>
    <thead><tr><th>Field</th><th>Status</th><th>Risk</th></tr></thead>
    <tbody>
      <tr><td>payer</td><td>MISSING_IN_MART</td><td>No payer-specific intervention claims</td></tr>
      <tr><td>service_date</td><td>Proxy from aging_days</td><td>Use for ranking, not adjudication timing</td></tr>
      <tr><td>denied_amount</td><td>Proxy from denied_potential_allowed_proxy_amt</td><td>Directional only</td></tr>
    </tbody>
  </table>
  <h2>Outcomes snapshot</h2>
  <ul>{metrics_block}</ul>
  <p>Source: <code>{escape(source_fqn)}</code></p>
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
    outcomes_metrics: dict[str, float] | None,
    capacity_summary: dict[str, float | str | bool],
    impact: dict[str, object],
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
            "- Opportunity sizing CSV: `exports/denials_recovery_opportunity_sizing_v1.csv`",
        ]
    )

    lines.extend(
        [
            "",
            "## Opportunity & Capacity (Directional)",
            f"- Weekly touch budget: **{float(capacity_summary['weekly_touch_budget_minutes'])/60.0:.1f} hours**",
            f"- Effective touch minutes: **{float(capacity_summary['effective_touch_minutes']):.1f}**",
            f"- Expected touches/week: **{float(capacity_summary['expected_touches']):.1f}**",
        ]
    )
    if bool(capacity_summary["has_outcomes"]):
        lines.extend(
            [
                f"- Expected resolutions/week: **{float(capacity_summary['expected_resolutions']):.1f}**",
                f"- Expected recovered amount/week: **{_fmt_money(float(capacity_summary['expected_recovered_amt']))}** (directional)",
            ]
        )
    else:
        lines.extend(
            [
                "- No outcomes file provided: capacity outputs are directional placeholders.",
            ]
        )

    lines.extend(["", "## Outcome Tracking (Learning Loop)"])
    if outcomes_metrics is None:
        lines.extend(
            [
                "- No outcomes file provided yet (`--outcomes-csv` not supplied).",
                "- Outcomes remain directional until sourced from adjudication/ERA-quality systems.",
            ]
        )
    else:
        lines.extend(
            [
                "- Outcomes are directional unless sourced from adjudication/ERA-grade systems.",
                f"- Outcomes rows: **{int(outcomes_metrics['outcomes_rows'])}**",
                f"- Matched claims: **{int(outcomes_metrics['matched_claims'])}**",
                f"- Recovery realized sum: **{_fmt_money(outcomes_metrics['recovery_realized_sum'])}**",
                f"- Recovery realized rate: **{_fmt_pct(outcomes_metrics['recovery_realized_rate'])}**",
                f"- Resolved rate: **{_fmt_pct(outcomes_metrics['resolved_rate'])}**",
                f"- False positive rate: **{_fmt_pct(outcomes_metrics['false_positive_rate'])}**",
                f"- Top-bucket recovery rate: **{_fmt_pct(outcomes_metrics['top_bucket_recovery_rate'])}**",
                "- Guardrail: do not overclaim ROI from proxy-based outcomes.",
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


def _prepare_outcomes_input(outcomes_raw: pd.DataFrame, claim_id_col: str) -> pd.DataFrame:
    if claim_id_col not in outcomes_raw.columns:
        raise RuntimeError(f"Outcomes file missing claim id column: {claim_id_col}")
    df = outcomes_raw.copy()
    if "claim_id" not in df.columns:
        df = df.rename(columns={claim_id_col: "claim_id"})
    df["claim_id"] = df["claim_id"].astype(str).str.strip()
    for col in ["resolution_status", "resolution_type", "notes"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.strip()
    if "realized_recovery_amt" not in df.columns:
        df["realized_recovery_amt"] = 0.0
    df["realized_recovery_amt"] = pd.to_numeric(df["realized_recovery_amt"], errors="coerce").fillna(0.0)
    if "resolved_date" not in df.columns:
        df["resolved_date"] = pd.NaT
    df["resolved_date"] = pd.to_datetime(df["resolved_date"], errors="coerce")
    # Keep one deterministic row per claim_id (latest resolved_date, then status/type lexical)
    df = df.sort_values(
        ["claim_id", "resolved_date", "resolution_status", "resolution_type"],
        ascending=[True, False, True, True],
        na_position="last",
    )
    return df.drop_duplicates(subset=["claim_id"], keep="first").reset_index(drop=True)


def _build_outcomes_export(
    workqueue_out: pd.DataFrame,
    outcomes_in: pd.DataFrame,
    run_anchor_date: date,
    outcomes_window_days: int,
    top2_buckets: set[str],
) -> tuple[pd.DataFrame, dict[str, float]]:
    out = workqueue_out.copy()
    out["claim_id"] = out["claim_id"].astype(str)
    joined = out.merge(
        outcomes_in[
            ["claim_id", "resolution_status", "resolution_type", "resolved_date", "realized_recovery_amt", "notes"]
        ],
        on="claim_id",
        how="left",
    )
    joined["resolved_date"] = pd.to_datetime(joined["resolved_date"], errors="coerce")
    joined["realized_recovery_amt"] = pd.to_numeric(joined["realized_recovery_amt"], errors="coerce").fillna(0.0)
    joined["resolution_status"] = joined["resolution_status"].fillna("").astype(str)
    joined["resolution_type"] = joined["resolution_type"].fillna("").astype(str)

    joined["is_resolved"] = joined["resolution_status"].str.upper().isin(
        {"RECOVERED", "WRITTEN_OFF", "DENIED_FINAL"}
    )
    joined["is_recovered"] = (
        joined["resolution_status"].str.upper().eq("RECOVERED")
        & (joined["realized_recovery_amt"] > 0)
    )
    joined["recovery_lift_ratio"] = (
        joined["realized_recovery_amt"] / joined["denied_amount"].replace(0, pd.NA)
    ).fillna(0.0)
    joined["recovery_lift_ratio"] = joined["recovery_lift_ratio"].clip(lower=0.0, upper=1.0)
    joined["days_to_resolve"] = (
        joined["resolved_date"] - pd.Timestamp(run_anchor_date)
    ).dt.days

    matched_mask = joined["resolution_status"].str.len() > 0
    matched = joined[matched_mask].copy()
    resolved_within_window = matched["days_to_resolve"].abs().le(outcomes_window_days)
    recovered_mask = matched["is_recovered"]
    resolved_mask = matched["is_resolved"] & resolved_within_window.fillna(False)
    false_positive_mask = resolved_mask & (~recovered_mask)

    matched_denied_sum = float(matched["denied_amount"].sum()) if not matched.empty else 0.0
    realized_sum = float(matched.loc[recovered_mask, "realized_recovery_amt"].sum()) if not matched.empty else 0.0
    resolved_rate = (float(resolved_mask.mean()) if len(matched) > 0 else 0.0)
    false_positive_rate = (float(false_positive_mask.mean()) if len(matched) > 0 else 0.0)
    recovery_realized_rate = (realized_sum / matched_denied_sum) if matched_denied_sum > 0 else 0.0

    top_bucket_subset = matched[matched["denial_bucket"].isin(top2_buckets)]
    top_bucket_recovery_rate = (
        float(top_bucket_subset["is_recovered"].mean()) if len(top_bucket_subset) > 0 else 0.0
    )

    metrics = {
        "outcomes_rows": float(len(outcomes_in)),
        "matched_claims": float(len(matched)),
        "recovery_realized_sum": realized_sum,
        "recovery_realized_rate": recovery_realized_rate,
        "resolved_rate": resolved_rate,
        "false_positive_rate": false_positive_rate,
        "top_bucket_recovery_rate": top_bucket_recovery_rate,
    }

    export_df = joined[
        [
            "claim_id",
            "dataset_week_key",
            "denial_bucket",
            "denied_amount",
            "recovery_priority_score",
            "owner",
            "resolution_status",
            "resolution_type",
            "resolved_date",
            "realized_recovery_amt",
            "is_resolved",
            "is_recovered",
            "recovery_lift_ratio",
            "days_to_resolve",
            "notes",
        ]
    ].copy()
    export_df["resolved_date"] = pd.to_datetime(export_df["resolved_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    export_df["resolved_date"] = export_df["resolved_date"].fillna("")
    export_df["is_resolved"] = export_df["is_resolved"].map({True: "Y", False: "N"})
    export_df["is_recovered"] = export_df["is_recovered"].map({True: "Y", False: "N"})
    export_df = export_df.sort_values(
        ["recovery_priority_score", "claim_id"],
        ascending=[False, True],
    ).reset_index(drop=True)
    return export_df, metrics


def _build_opportunity_sizing(
    workqueue_out: pd.DataFrame,
    outcomes_export: pd.DataFrame | None,
) -> pd.DataFrame:
    base = (
        workqueue_out.groupby("denial_bucket", as_index=False)
        .agg(
            workqueue_denied_sum=("denied_amount", "sum"),
            workqueue_count=("claim_id", "size"),
            avg_denied=("denied_amount", "mean"),
        )
        .sort_values(["workqueue_denied_sum", "denial_bucket"], ascending=[False, True])
        .reset_index(drop=True)
    )

    if outcomes_export is None or outcomes_export.empty:
        base["resolved_rate"] = pd.NA
        base["recovered_rate"] = pd.NA
        base["avg_realized_recovery_amt"] = pd.NA
        base["expected_recovered_per_10_touches"] = pd.NA
        return base[
            [
                "denial_bucket",
                "workqueue_denied_sum",
                "workqueue_count",
                "avg_denied",
                "resolved_rate",
                "recovered_rate",
                "avg_realized_recovery_amt",
                "expected_recovered_per_10_touches",
            ]
        ]

    matched = outcomes_export[outcomes_export["resolution_status"].astype(str).str.len() > 0].copy()
    matched["is_resolved_bool"] = matched["is_resolved"].eq("Y")
    matched["is_recovered_bool"] = matched["is_recovered"].eq("Y")
    matched["realized_recovery_amt"] = pd.to_numeric(
        matched["realized_recovery_amt"], errors="coerce"
    ).fillna(0.0)

    by_bucket = (
        matched.groupby("denial_bucket", as_index=False)
        .agg(
            resolved_rate=("is_resolved_bool", "mean"),
            recovered_rate=("is_recovered_bool", "mean"),
            avg_realized_recovery_amt=("realized_recovery_amt", "mean"),
        )
        .sort_values(["denial_bucket"], ascending=[True])
        .reset_index(drop=True)
    )
    by_bucket["expected_recovered_per_10_touches"] = (
        by_bucket["recovered_rate"] * by_bucket["avg_realized_recovery_amt"] * 10.0
    )

    merged = base.merge(by_bucket, on="denial_bucket", how="left")
    return merged[
        [
            "denial_bucket",
            "workqueue_denied_sum",
            "workqueue_count",
            "avg_denied",
            "resolved_rate",
            "recovered_rate",
            "avg_realized_recovery_amt",
            "expected_recovered_per_10_touches",
        ]
    ].sort_values(["workqueue_denied_sum", "denial_bucket"], ascending=[False, True]).reset_index(drop=True)


def _parse_touch_minutes_by_bucket(raw: str) -> dict[str, float]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in --touch-minutes-by-bucket: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("--touch-minutes-by-bucket must be a JSON object")
    clean: dict[str, float] = {}
    for key, value in parsed.items():
        try:
            v = float(value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Invalid touch minute value for bucket '{key}'") from exc
        if v <= 0:
            raise RuntimeError(f"Touch minutes must be positive for bucket '{key}'")
        clean[str(key)] = v
    return clean


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
    parser.add_argument("--outcomes-csv", type=str, default="", help="Optional outcomes CSV path for realized feedback metrics.")
    parser.add_argument("--outcomes-claim-id-col", type=str, default="claim_id", help="Claim id column name in outcomes CSV.")
    parser.add_argument("--outcomes-window-days", type=int, default=90, help="Window for recovered/resolved-within metrics.")
    parser.add_argument("--touch-minutes-default", type=float, default=12.0, help="Default touch minutes per claim.")
    parser.add_argument(
        "--touch-minutes-by-bucket",
        type=str,
        default="",
        help='Optional JSON map like {"AUTH_ELIG":10,"CODING_DOC":14}',
    )
    parser.add_argument("--weekly-touch-budget-minutes", type=float, default=600.0, help="Weekly touch budget in minutes.")
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

    out_dir = Path(args.out)
    docs_dir = Path("docs")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "denials_recovery_summary_v1.csv"
    workqueue_path = out_dir / "denials_recovery_workqueue_v1.csv"
    aging_path = out_dir / "denials_recovery_aging_bands_v1.csv"
    stability_path = out_dir / "denials_recovery_stability_v1.csv"
    outcomes_path = out_dir / "denials_recovery_outcomes_v1.csv"
    opportunity_sizing_path = out_dir / "denials_recovery_opportunity_sizing_v1.csv"
    teaching_html_path = out_dir / "denials_recovery_brief_v1_teaching.html"

    aging_df = _build_aging_bands(current_df)
    stability_df, top2_overlap = _compute_stability(current_df, prior_df)

    _write_csv(summary_out, summary_path)
    _write_csv(workqueue_out, workqueue_path)
    _write_csv(aging_df, aging_path)
    _write_csv(stability_df, stability_path)

    current_key_str = _dataset_week_from_value(current_dataset_week_key)
    prior_key_str = _dataset_week_from_value(prior_dataset_week_key) if prior_dataset_week_key else "NONE"
    top2_buckets = set(summary_out.head(2)["denial_bucket"].tolist())
    top2_rows = summary_out.head(2).copy()
    current_total_denied_amount_sum = float(summary_out["denied_amount_sum"].sum()) if not summary_out.empty else 0.0
    current_total_priority_score_sum = float(summary_out["priority_score"].sum()) if not summary_out.empty else 0.0
    top2_priority_sum = float(top2_rows["priority_score"].sum()) if not top2_rows.empty else 0.0
    top2_denied_sum = float(top2_rows["denied_amount_sum"].sum()) if not top2_rows.empty else 0.0
    top2_priority_share_pct = (top2_priority_sum / current_total_priority_score_sum * 100.0) if current_total_priority_score_sum > 0 else 0.0
    top2_denied_amount_share_pct = (top2_denied_sum / current_total_denied_amount_sum * 100.0) if current_total_denied_amount_sum > 0 else 0.0
    top2_bucket_names = ", ".join(top2_rows["denial_bucket"].astype(str).tolist()) if not top2_rows.empty else "NONE"
    impact: dict[str, object] = {
        "current_week_key": current_key_str,
        "prior_week_key": prior_key_str,
        "current_total_denied_amount_sum": current_total_denied_amount_sum,
        "current_total_priority_score_sum": current_total_priority_score_sum,
        "top2_priority_share_pct": top2_priority_share_pct,
        "top2_denied_amount_share_pct": top2_denied_amount_share_pct,
        "workqueue_size_used": int(len(workqueue_out)),
        "top2_bucket_names": top2_bucket_names,
        "top2_overlap": int(top2_overlap),
        "confidence_signal": "LOW",
        "expected_recovery_amt": 0.0,
        "outcomes_sample_n": 0,
        "sample_quality": "NO_OUTCOMES_PROVIDED",
    }
    outcomes_metrics: dict[str, float] | None = None
    outcomes_export: pd.DataFrame | None = None
    if args.outcomes_csv:
        outcomes_csv_path = Path(args.outcomes_csv)
        if outcomes_csv_path.exists():
            outcomes_raw = pd.read_csv(outcomes_csv_path)
            outcomes_in = _prepare_outcomes_input(outcomes_raw, args.outcomes_claim_id_col)
            outcomes_export, outcomes_metrics = _build_outcomes_export(
                workqueue_out=workqueue_out,
                outcomes_in=outcomes_in,
                run_anchor_date=anchor_date,
                outcomes_window_days=args.outcomes_window_days,
                top2_buckets=top2_buckets,
            )
            _write_csv(outcomes_export, outcomes_path)
        else:
            print(f"OUTCOMES_WARNING=File not found: {outcomes_csv_path}")

    touch_map = _parse_touch_minutes_by_bucket(args.touch_minutes_by_bucket)
    touch_series = workqueue_out["denial_bucket"].map(lambda b: touch_map.get(str(b), float(args.touch_minutes_default)))
    effective_touch_minutes = float(touch_series.mean()) if len(touch_series) > 0 else float(args.touch_minutes_default)
    weekly_touch_budget_minutes = float(args.weekly_touch_budget_minutes)
    expected_touches = weekly_touch_budget_minutes / effective_touch_minutes if effective_touch_minutes > 0 else 0.0
    has_outcomes = outcomes_metrics is not None and outcomes_export is not None
    resolved_rate = float(outcomes_metrics["resolved_rate"]) if outcomes_metrics is not None else 0.0
    if outcomes_export is not None:
        recovered_rows = outcomes_export[outcomes_export["is_recovered"].eq("Y")]
        avg_realized_per_resolved = (
            float(pd.to_numeric(recovered_rows["realized_recovery_amt"], errors="coerce").fillna(0.0).mean())
            if len(recovered_rows) > 0
            else 0.0
        )
    else:
        avg_realized_per_resolved = 0.0
    expected_resolutions = expected_touches * resolved_rate if has_outcomes else 0.0
    expected_recovered_amt = expected_resolutions * avg_realized_per_resolved if has_outcomes else 0.0
    outcomes_sample_n = int(outcomes_metrics["matched_claims"]) if outcomes_metrics is not None else 0
    if outcomes_metrics is None:
        sample_quality = "NO_OUTCOMES_PROVIDED"
    else:
        sample_quality = "OK" if outcomes_sample_n >= 30 else "LOW"
    confidence_signal = _impact_confidence_label(top2_overlap, outcomes_sample_n)
    impact["expected_recovery_amt"] = expected_recovered_amt if has_outcomes else 0.0
    impact["outcomes_sample_n"] = outcomes_sample_n
    impact["sample_quality"] = sample_quality
    impact["confidence_signal"] = confidence_signal
    capacity_summary: dict[str, float | str | bool] = {
        "weekly_touch_budget_minutes": weekly_touch_budget_minutes,
        "effective_touch_minutes": effective_touch_minutes,
        "expected_touches": expected_touches,
        "expected_resolutions": expected_resolutions,
        "expected_recovered_amt": expected_recovered_amt,
        "has_outcomes": has_outcomes,
    }

    opportunity_sizing_df = _build_opportunity_sizing(workqueue_out, outcomes_export)
    _write_csv(opportunity_sizing_df, opportunity_sizing_path)

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
        outcomes_metrics=outcomes_metrics,
        capacity_summary=capacity_summary,
        impact=impact,
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
    teaching_html_path.write_text(
        _build_teaching_html(
            source_fqn=source_fqn,
            anchor_mode=anchor_mode,
            current_week_key=current_key_str,
            prior_week_key=prior_key_str,
            summary_df=summary_out,
            outcomes_metrics=outcomes_metrics,
            impact=impact,
        ),
        encoding="utf-8",
    )

    if args.write_html:
        html_text = _to_html_document(
            "Denials Recovery Opportunity Brief v1",
            markdown,
            shares,
            opportunity_sizing_df,
            capacity_summary,
            impact,
        )
        brief_html_path.write_text(html_text, encoding="utf-8")
        if args.determinism_check:
            first_hash = _sha256(brief_html_path)
            brief_html_path.write_text(
                _to_html_document(
                    "Denials Recovery Opportunity Brief v1",
                    markdown,
                    shares,
                    opportunity_sizing_df,
                    capacity_summary,
                    impact,
                ),
                encoding="utf-8",
            )
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
    print(f"IMPACT_WEEK_CURRENT={current_key_str}")
    print(f"IMPACT_WEEK_PRIOR={prior_key_str}")
    print(f"IMPACT_TOTAL_DENIED_PROXY={current_total_denied_amount_sum:.2f}")
    print(f"IMPACT_TOTAL_PRIORITY_SCORE={current_total_priority_score_sum:.2f}")
    print(f"IMPACT_TOP2_BUCKETS={top2_bucket_names}")
    print(f"IMPACT_TOP2_PRIORITY_SHARE={top2_priority_share_pct:.4f}%")
    print(f"IMPACT_TOP2_OVERLAP={top2_overlap}/2")
    print(f"IMPACT_CONFIDENCE={impact['confidence_signal']}")
    print(f"IMPACT_WORKQUEUE_SIZE={int(len(workqueue_out))}")
    if outcomes_metrics is not None:
        print(f"IMPACT_EXPECTED_RECOVERY_AMT={expected_recovered_amt:.2f}")
        print(f"IMPACT_OUTCOMES_SAMPLE_N={outcomes_sample_n}")
        print(f"IMPACT_SAMPLE_QUALITY={sample_quality}")
    else:
        print("IMPACT_SAMPLE_QUALITY=NO_OUTCOMES_PROVIDED")
    print(f"CAPACITY_WEEKLY_TOUCH_BUDGET_MINUTES={weekly_touch_budget_minutes:.2f}")
    print(f"CAPACITY_TOUCH_MINUTES_DEFAULT={float(args.touch_minutes_default):.2f}")
    print(f"CAPACITY_EFFECTIVE_AVG_TOUCH_MINUTES={effective_touch_minutes:.2f}")
    print(f"CAPACITY_EXPECTED_TOUCHES={expected_touches:.2f}")
    if has_outcomes:
        print(f"CAPACITY_EXPECTED_RESOLUTIONS={expected_resolutions:.2f}")
        print(f"CAPACITY_EXPECTED_RECOVERED_AMT={expected_recovered_amt:.2f}")
    else:
        print("CAPACITY_OUTCOMES_STATUS=NO_OUTCOMES_PROVIDED")
    if outcomes_metrics is not None:
        print(f"OUTCOMES_ROWS={int(outcomes_metrics['outcomes_rows'])}")
        print(f"MATCHED_CLAIMS={int(outcomes_metrics['matched_claims'])}")
        print(f"RECOVERY_REALIZED_SUM={outcomes_metrics['recovery_realized_sum']:.2f}")
        print(f"RECOVERY_REALIZED_RATE={outcomes_metrics['recovery_realized_rate']:.4f}")
        print(f"RESOLVED_RATE={outcomes_metrics['resolved_rate']:.4f}")
        print(f"FALSE_POSITIVE_RATE={outcomes_metrics['false_positive_rate']:.4f}")
        print(f"TOP_BUCKET_RECOVERY_RATE={outcomes_metrics['top_bucket_recovery_rate']:.4f}")
    print(f"WROTE={summary_path}")
    print(f"WROTE={workqueue_path}")
    print(f"WROTE={aging_path}")
    print(f"WROTE={stability_path}")
    print(f"WROTE={opportunity_sizing_path}")
    if outcomes_metrics is not None:
        print(f"WROTE={outcomes_path}")
    print(f"WROTE={brief_md_path}")
    if args.write_html:
        print(f"WROTE={brief_html_path}")
    print(f"WROTE={teaching_html_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
