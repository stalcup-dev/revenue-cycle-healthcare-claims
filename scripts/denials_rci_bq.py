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
    COALESCE(top_denial_group, 'UNSPECIFIED') AS top_denial_group,
    COALESCE(top_denial_prcsg, '') AS top_denial_prcsg,
    COALESCE(top_next_best_action, '') AS top_next_best_action,
    COALESCE(top_hcpcs, '') AS top_hcpcs,
    COALESCE(denied_potential_allowed_proxy_amt, 0.0) AS denied_amount_proxy,
    COALESCE(p_denial, 0.0) AS p_denial,
    LOWER(
      CONCAT(
        COALESCE(top_denial_group, ''),
        ' ',
        COALESCE(top_denial_prcsg, ''),
        ' ',
        COALESCE(top_next_best_action, '')
      )
    ) AS denial_reason_text
  FROM `{source_fqn}`
  WHERE CAST(COALESCE(aging_days, 0) AS INT64) BETWEEN @min_aging_days AND (@min_aging_days + @lookback_days)
),
denied AS (
  SELECT
    *,
    (
      p_denial > 0
      OR top_denial_prcsg != ''
      OR top_denial_group != 'UNSPECIFIED'
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
    END AS denial_bucket,
    CASE
      WHEN REGEXP_CONTAINS(denial_reason_text, r'auth|authorization|precert|elig|eligibility|coverage|member') THEN 1.0
      WHEN REGEXP_CONTAINS(denial_reason_text, r'coding|modifier|dx|icd|cpt|documentation|medical record|bundl') THEN 1.0
      WHEN REGEXP_CONTAINS(denial_reason_text, r'timely|filing|limit|late') THEN 1.0
      WHEN REGEXP_CONTAINS(denial_reason_text, r'duplicate|dup') THEN 1.0
      WHEN REGEXP_CONTAINS(denial_reason_text, r'contract|noncovered|non-covered|bundled per contract|write off') THEN 0.2
      ELSE 0.6
    END AS preventability_weight
  FROM denied
  WHERE denial_flag
)
SELECT
  claim_id,
  service_date,
  dataset_week_key,
  aging_days,
  top_denial_group,
  top_denial_prcsg,
  top_next_best_action,
  top_hcpcs,
  denied_amount_proxy,
  p_denial,
  denial_bucket,
  preventability_weight,
  LOWER(
    CONCAT(
      COALESCE(top_denial_group, ''),
      ' | ',
      COALESCE(top_denial_prcsg, ''),
      ' | ',
      COALESCE(top_next_best_action, '')
    )
  ) AS pattern_text,
  LOWER(COALESCE(top_next_best_action, '')) AS next_action_text
FROM bucketed
ORDER BY dataset_week_key DESC, denied_amount_proxy DESC, claim_id
"""


ACTION_CATEGORY_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("AUTH_REQUIRED", re.compile(r"auth|authorization|precert")),
    ("ELIGIBILITY", re.compile(r"elig|eligibility|coverage|member")),
    ("CODING_MODIFIER", re.compile(r"coding|modifier|dx|icd|cpt")),
    ("MEDICAL_RECORDS", re.compile(r"medical|record|documentation|op note")),
    ("TIMELY_FILING", re.compile(r"timely|filing|limit|late")),
    ("DUPLICATE", re.compile(r"duplicate|dup")),
    ("CONTRACTUAL", re.compile(r"contract|noncovered|non-covered|write off|allow")),
]

OWNER_MAP = {
    "AUTH_REQUIRED": "Eligibility/Auth team",
    "ELIGIBILITY": "Eligibility/Auth team",
    "CODING_MODIFIER": "Coding/CDI",
    "MEDICAL_RECORDS": "Coding/CDI",
    "TIMELY_FILING": "Billing",
    "DUPLICATE": "Billing",
    "CONTRACTUAL": "Contracting/RCM lead",
    "OTHER_ACTION": "RCM analyst review",
}

EVIDENCE_MAP = {
    "AUTH_REQUIRED": "auth number; prior auth request log",
    "ELIGIBILITY": "eligibility response; coverage verification timestamp",
    "CODING_MODIFIER": "coded claim detail; coding notes",
    "MEDICAL_RECORDS": "clinical documentation excerpt; submission packet",
    "TIMELY_FILING": "submission timestamp; payer filing limit policy",
    "DUPLICATE": "claim history; duplicate match proof",
    "CONTRACTUAL": "contract clause excerpt; allowed schedule",
    "OTHER_ACTION": "manual triage notes; payer response detail",
}

UPSTREAM_FIX_MAP = {
    "AUTH_REQUIRED": "Pre-bill authorization hard-stop with exception logging.",
    "ELIGIBILITY": "Real-time eligibility refresh before claim finalization.",
    "CODING_MODIFIER": "Targeted edit rules for recurring coding/modifier patterns.",
    "MEDICAL_RECORDS": "Attach required documentation bundle at first submission.",
    "TIMELY_FILING": "Age-based filing-limit alerts with escalation queue.",
    "DUPLICATE": "Duplicate fingerprint check before outbound claim submission.",
    "CONTRACTUAL": "Contract reference table linked to denial routing rules.",
    "OTHER_ACTION": "Expand denial reason standardization dictionary.",
}

LEVER_MAP = {
    "AUTH_REQUIRED": "Add pre-bill auth gate and exception queue.",
    "ELIGIBILITY": "Run same-day eligibility reverification before submit.",
    "CODING_MODIFIER": "Apply coding edit rules for recurring modifier/dx misses.",
    "MEDICAL_RECORDS": "Attach required clinical packet at first submission.",
    "TIMELY_FILING": "Escalate aging claims before filing-limit threshold.",
    "DUPLICATE": "Enable duplicate fingerprint check pre-submit.",
    "CONTRACTUAL": "Route contractual disputes to contract variance review.",
    "OTHER_ACTION": "Manual triage and classify to reduce OTHER_ACTION share.",
}

KPI_MAP = {
    "AUTH_REQUIRED": "Auth pass rate before submission",
    "ELIGIBILITY": "Eligibility pass rate before submission",
    "CODING_MODIFIER": "Coding correction hit rate",
    "MEDICAL_RECORDS": "Documentation completeness on first pass",
    "TIMELY_FILING": "Filing-timeliness compliance",
    "DUPLICATE": "Duplicate-denial recurrence rate",
    "CONTRACTUAL": "Contract variance resolution rate",
    "OTHER_ACTION": "Unclassified denial share",
}


def _fmt_money(value: float) -> str:
    return f"${value:,.0f}"


def _fmt_pct(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def _safe_md_cell(value: object) -> str:
    text = str(value) if value is not None else ""
    return text.replace("|", " / ").replace("\n", " ").strip()


def _run_query(client: bigquery.Client, sql: str, params: list[bigquery.ScalarQueryParameter]) -> pd.DataFrame:
    cfg = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(sql, job_config=cfg).result().to_dataframe()


def _assign_action_category(action_text: str, pattern_text: str) -> str:
    text = f"{action_text or ''} {pattern_text or ''}"
    for label, pattern in ACTION_CATEGORY_RULES:
        if pattern.search(text):
            return label
    return "OTHER_ACTION"


def _markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    html: list[str] = []
    in_list = False
    in_table = False
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            if in_list:
                html.append("</ul>")
                in_list = False
            if in_table:
                html.append("</tbody></table>")
                in_table = False
            continue
        if s.startswith("# "):
            html.append(f"<h1>{escape(s[2:])}</h1>")
            continue
        if s.startswith("## "):
            html.append(f"<h2>{escape(s[3:])}</h2>")
            continue
        if s.startswith("### "):
            html.append(f"<h3>{escape(s[4:])}</h3>")
            continue
        if s.startswith("- "):
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{escape(s[2:])}</li>")
            continue
        if s.startswith("|") and s.endswith("|"):
            parts = [p.strip() for p in s.strip("|").split("|")]
            # skip markdown alignment row
            if all(re.fullmatch(r":?-{3,}:?", p) for p in parts):
                continue
            if not in_table:
                html.append("<table><thead><tr>" + "".join(f"<th>{escape(p)}</th>" for p in parts) + "</tr></thead><tbody>")
                in_table = True
            else:
                html.append("<tr>" + "".join(f"<td>{escape(p)}</td>" for p in parts) + "</tr>")
            continue
        html.append(f"<p>{escape(s)}</p>")

    if in_list:
        html.append("</ul>")
    if in_table:
        html.append("</tbody></table>")
    return "\n".join(html)


def _to_html_document(title: str, content_html: str, visual_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ max-width: 980px; margin: 24px auto; padding: 0 16px 40px; font-family: Segoe UI, Arial, sans-serif; line-height: 1.5; color:#111; }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0 16px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    .visual-card {{ border: 1px solid #d0d7de; border-radius: 8px; padding: 12px; margin: 8px 0 18px; background: #fafcff; }}
    .bar-row {{ display: grid; grid-template-columns: 320px 1fr 70px; gap: 8px; align-items: center; margin: 6px 0; }}
    .bar-label {{ font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .bar-track {{ width: 100%; height: 14px; border: 1px solid #d0d7de; border-radius: 3px; overflow: hidden; background: #f6f8fa; }}
    .bar-fill {{ height: 100%; background: #1f77b4; }}
    .bar-pct {{ font-size: 12px; text-align: right; color: #374151; }}
    .stacked-bar {{ display: flex; width: 100%; height: 18px; border: 1px solid #d0d7de; border-radius: 4px; overflow: hidden; margin: 8px 0 8px; }}
    .stacked-legend {{ font-size: 12px; color: #374151; margin-bottom: 12px; }}
    .mix-grid table {{ margin-top: 8px; }}
    .heat-cell {{ font-weight: 600; text-align: center; }}
  </style>
</head>
<body>
  {visual_html}
  {content_html}
</body>
</html>
"""


def _build_visual_html(
    patterns_overall: pd.DataFrame,
    summary_out: pd.DataFrame,
    pattern_grouped: pd.DataFrame,
) -> str:
    top5 = patterns_overall.head(5).copy()
    total = float(patterns_overall["denied_amount_sum"].sum()) if not patterns_overall.empty else 0.0
    shown = float(top5["denied_amount_sum"].sum()) if not top5.empty else 0.0
    other = max(0.0, total - shown)

    rows: list[str] = []
    for _, row in top5.iterrows():
        amt = float(row["denied_amount_sum"])
        share = amt / total if total > 0 else 0.0
        width = share * 100.0
        rows.append(
            "<div class='bar-row'>"
            + f"<div class='bar-label'>{escape(str(row['pattern_text']))}</div>"
            + f"<div class='bar-track'><div class='bar-fill' style='width:{width:.2f}%;'></div></div>"
            + f"<div class='bar-pct'>{_fmt_pct(share)}</div>"
            + "</div>"
        )

    if other > 0 and total > 0:
        share = other / total
        rows.append(
            "<div class='bar-row'>"
            + "<div class='bar-label'>Other</div>"
            + f"<div class='bar-track'><div class='bar-fill' style='width:{share * 100.0:.2f}%; background:#9ca3af;'></div></div>"
            + f"<div class='bar-pct'>{_fmt_pct(share)}</div>"
            + "</div>"
        )

    pareto_html = "<div class='visual-card'><h2>Pareto (Top 5 patterns overall)</h2>" + "".join(rows) + "</div>"

    # Bucket concentration stacked bar (top buckets + remainder)
    bucket_rows = (
        summary_out[["denial_bucket", "share"]]
        .sort_values(["share", "denial_bucket"], ascending=[False, True], kind="mergesort")
        .head(5)
        .copy()
    )
    bucket_used = float(bucket_rows["share"].sum()) if not bucket_rows.empty else 0.0
    bucket_remainder = max(0.0, 1.0 - bucket_used)
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b", "#9ca3af"]
    stacked_parts: list[str] = []
    legend_parts: list[str] = []
    for idx, row in bucket_rows.reset_index(drop=True).iterrows():
        share = float(row["share"])
        color = palette[idx % len(palette)]
        stacked_parts.append(f'<span style="width:{share * 100.0:.2f}%;background:{color};"></span>')
        legend_parts.append(
            f'<span style="margin-right:12px;"><span style="display:inline-block;width:10px;height:10px;background:{color};margin-right:4px;"></span>{escape(str(row["denial_bucket"]))} ({_fmt_pct(share)})</span>'
        )
    if bucket_remainder > 1e-9:
        stacked_parts.append(f'<span style="width:{bucket_remainder * 100.0:.2f}%;background:{palette[-1]};"></span>')
        legend_parts.append(
            f'<span style="margin-right:12px;"><span style="display:inline-block;width:10px;height:10px;background:{palette[-1]};margin-right:4px;"></span>Remainder ({_fmt_pct(bucket_remainder)})</span>'
        )
    bucket_html = (
        "<div class='visual-card'>"
        "<h2>Bucket concentration</h2>"
        "<div class='stacked-bar'>"
        + "".join(stacked_parts)
        + "</div>"
        + "<div class='stacked-legend'>"
        + "".join(legend_parts)
        + "</div>"
        + "<p><em>directional signal from proxies</em></p>"
        + "</div>"
    )

    # Pattern mix grid for top 2 buckets x top action categories
    top_buckets = (
        summary_out.sort_values(["rank", "denial_bucket"], ascending=[True, True], kind="mergesort")
        .head(2)["denial_bucket"]
        .tolist()
    )
    mix_base = pattern_grouped[pattern_grouped["denial_bucket"].isin(top_buckets)].copy()
    mix_agg = (
        mix_base.groupby(["denial_bucket", "action_category"], as_index=False)
        .agg(denied_amount_sum=("denied_amount_sum", "sum"))
        .sort_values(["denied_amount_sum", "action_category"], ascending=[False, True], kind="mergesort")
    )
    top_actions = mix_agg["action_category"].drop_duplicates().head(4).tolist()
    if len(top_actions) < 3:
        all_actions = (
            pattern_grouped["action_category"]
            .drop_duplicates()
            .sort_values(kind="mergesort")
            .tolist()
        )
        for action in all_actions:
            if action not in top_actions:
                top_actions.append(action)
            if len(top_actions) >= 3:
                break
    top_actions = top_actions[:4]
    mix_rows: list[str] = []
    for bucket in top_buckets:
        bucket_total = float(mix_base[mix_base["denial_bucket"] == bucket]["denied_amount_sum"].sum())
        row_cells = [f"<td>{escape(bucket)}</td>"]
        for action in top_actions:
            amt = float(
                mix_base[
                    (mix_base["denial_bucket"] == bucket) & (mix_base["action_category"] == action)
                ]["denied_amount_sum"].sum()
            )
            share = (amt / bucket_total) if bucket_total > 0 else 0.0
            alpha = 0.10 + (0.70 * share)
            cell_style = f"background: rgba(31,119,180,{alpha:.3f});"
            row_cells.append(f"<td class='heat-cell' style='{cell_style}'>{_fmt_pct(share)}</td>")
        mix_rows.append("<tr>" + "".join(row_cells) + "</tr>")

    mix_header = "<tr><th>denial_bucket</th>" + "".join(f"<th>{escape(a)}</th>" for a in top_actions) + "</tr>"
    mix_html = (
        "<div class='visual-card mix-grid'>"
        "<h2>Pattern mix (bucket × action category)</h2>"
        "<table><thead>"
        + mix_header
        + "</thead><tbody>"
        + "".join(mix_rows)
        + "</tbody></table>"
        + "<p><em>not a causal claim</em></p>"
        + "</div>"
    )

    # Owner workload bars (directional touches proxy)
    owner_workload = (
        pattern_grouped.groupby("owner", as_index=False)
        .agg(denial_count=("denial_count", "sum"))
        .sort_values(["denial_count", "owner"], ascending=[False, True], kind="mergesort")
        .head(5)
        .reset_index(drop=True)
    )
    max_count = float(owner_workload["denial_count"].max()) if not owner_workload.empty else 1.0
    owner_rows: list[str] = []
    for _, row in owner_workload.iterrows():
        count = int(row["denial_count"])
        width = (count / max_count * 100.0) if max_count > 0 else 0.0
        owner_rows.append(
            "<div class='bar-row'>"
            + f"<div class='bar-label'>{escape(str(row['owner']))}</div>"
            + f"<div class='bar-track'><div class='bar-fill' style='width:{width:.2f}%; background:#2563eb;'></div></div>"
            + f"<div class='bar-pct'>{count}</div>"
            + "</div>"
        )
    owner_html = (
        "<div class='visual-card'>"
        "<h2>Owner workload (directional)</h2>"
        "<p><strong>Metric: denial_count (claims) - directional estimate</strong></p>"
        + "".join(owner_rows)
        + "<p><em>directional workload estimate</em></p>"
        + "</div>"
    )

    monday_html = (
        "<div class='visual-card'>"
        "<h2>What to do Monday</h2>"
        "<p>Use the operational ticket pack: "
        "<a href='denials_rci_ticket_pack_v1.html'>docs/denials_rci_ticket_pack_v1.html</a>.</p>"
        "<p><em>Route top patterns to owners with evidence-first execution.</em></p>"
        "</div>"
    )

    return pareto_html + bucket_html + mix_html + owner_html + monday_html


def _evidence_readiness_pct(evidence_text: str) -> int:
    parts = [p.strip() for p in str(evidence_text).split(";") if p.strip()]
    return min(100, len(parts) * 50)


def _build_ticket_pack(ticket_patterns: pd.DataFrame) -> pd.DataFrame:
    out = ticket_patterns.copy()
    if out.empty:
        return out

    total = float(out["denied_amount_sum"].sum())
    out = out.sort_values(
        ["denied_amount_sum", "denial_count", "pattern_text", "denial_bucket"],
        ascending=[False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    out["ticket_rank"] = out.index + 1
    out["operational_lever"] = out["action_category"].map(LEVER_MAP).fillna(LEVER_MAP["OTHER_ACTION"])
    out["kpi"] = out["action_category"].map(KPI_MAP).fillna(KPI_MAP["OTHER_ACTION"])
    out["impact_share"] = out["denied_amount_sum"] / total if total > 0 else 0.0
    out["evidence_readiness_pct"] = out["evidence_checklist"].map(_evidence_readiness_pct).astype(int)
    out["evidence_readiness"] = out["evidence_readiness_pct"].map(
        lambda x: "READY" if x >= 100 else ("PARTIAL" if x >= 50 else "WEAK")
    )
    out["payer_dim_status"] = "MISSING_IN_MART"
    return out[
        [
            "ticket_rank",
            "denial_bucket",
            "pattern_text",
            "action_category",
            "owner",
            "operational_lever",
            "evidence_checklist",
            "evidence_readiness_pct",
            "evidence_readiness",
            "kpi",
            "denied_amount_sum",
            "denial_count",
            "share_within_bucket",
            "impact_share",
            "payer_dim_status",
        ]
    ]


def _ticket_pack_markdown(source_fqn: str, current_week: date, tickets_df: pd.DataFrame) -> str:
    top10 = tickets_df.head(10).copy()
    owner_rollup = (
        top10.groupby("owner", as_index=False)
        .agg(ticket_count=("ticket_rank", "count"), denied_amount_sum=("denied_amount_sum", "sum"))
        .sort_values(["denied_amount_sum", "owner"], ascending=[False, True], kind="mergesort")
    )
    lines: list[str] = [
        "# Denials RCI Ticket Pack v1",
        "",
        f"Source: `{source_fqn}` (dbt mart only). Week key: `{pd.to_datetime(current_week).strftime('%Y-%m-%d')}`.",
        "",
        "## What to do Monday",
        "- Open the Top 10 pattern tickets below and assign each to the listed owner the same day.",
        "- Require listed evidence before changing workflow or escalation path.",
        "- Track the listed KPI weekly; if KPI does not improve, reclassify the pattern and lever.",
        "",
        "## Top 10 patterns -> owner -> lever -> evidence -> KPI",
        "| rank | denial_bucket | pattern_text | owner | operational_lever | evidence_checklist | KPI | impact_share |",
        "|---:|---|---|---|---|---|---|---:|",
    ]
    for _, row in top10.iterrows():
        lines.append(
            "| "
            + f"{int(row['ticket_rank'])} | {_safe_md_cell(row['denial_bucket'])} | {_safe_md_cell(row['pattern_text'])} | "
            + f"{_safe_md_cell(row['owner'])} | {_safe_md_cell(row['operational_lever'])} | {_safe_md_cell(row['evidence_checklist'])} | "
            + f"{_safe_md_cell(row['kpi'])} | {_fmt_pct(float(row['impact_share']))} |"
        )

    lines.extend(
        [
            "",
            "## Owner workload (directional)",
            "| owner | ticket_count | denied_amount_sum |",
            "|---|---:|---:|",
        ]
    )
    for _, row in owner_rollup.iterrows():
        lines.append(f"| {_safe_md_cell(row['owner'])} | {int(row['ticket_count'])} | {_fmt_money(float(row['denied_amount_sum']))} |")

    lines.extend(
        [
            "",
            "## Guardrails",
            "- Directional prioritization only; denied dollar values are proxies.",
            "- No payer identity claims; `payer_dim_status = MISSING_IN_MART`.",
            "- No date-dimension changes in this ticket pack slice.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _build_ticket_pack_visual_html(tickets_df: pd.DataFrame) -> str:
    top10 = tickets_df.head(10).copy()
    if top10.empty:
        return "<div class='visual-card'><h2>RCI Ticket Pack</h2><p>No ticket rows available.</p></div>"

    owner_rollup = (
        top10.groupby("owner", as_index=False)
        .agg(denial_count=("denial_count", "sum"))
        .sort_values(["denial_count", "owner"], ascending=[False, True], kind="mergesort")
        .head(5)
    )
    max_owner = float(owner_rollup["denial_count"].max()) if not owner_rollup.empty else 1.0
    owner_rows: list[str] = []
    for _, row in owner_rollup.iterrows():
        count = int(row["denial_count"])
        width = (count / max_owner * 100.0) if max_owner > 0 else 0.0
        owner_rows.append(
            "<div class='bar-row'>"
            + f"<div class='bar-label'>{escape(str(row['owner']))}</div>"
            + f"<div class='bar-track'><div class='bar-fill' style='width:{width:.2f}%; background:#1d4ed8;'></div></div>"
            + f"<div class='bar-pct'>{count} claims</div>"
            + "</div>"
        )

    impact_rows: list[str] = []
    max_share = float(top10["impact_share"].max()) if not top10.empty else 1.0
    for _, row in top10.iterrows():
        share = float(row["impact_share"])
        width = (share / max_share * 100.0) if max_share > 0 else 0.0
        impact_rows.append(
            "<div class='bar-row'>"
            + f"<div class='bar-label'>#{int(row['ticket_rank'])} {escape(str(row['denial_bucket']))}</div>"
            + f"<div class='bar-track'><div class='bar-fill' style='width:{width:.2f}%; background:#0ea5e9;'></div></div>"
            + f"<div class='bar-pct'>{_fmt_pct(share)}</div>"
            + "</div>"
        )

    readiness_rows: list[str] = []
    for _, row in top10.iterrows():
        pct = int(row["evidence_readiness_pct"])
        color = "#16a34a" if pct >= 100 else ("#f59e0b" if pct >= 50 else "#ef4444")
        readiness_rows.append(
            "<div class='bar-row'>"
            + f"<div class='bar-label'>#{int(row['ticket_rank'])} {escape(str(row['owner']))}</div>"
            + f"<div class='bar-track'><div class='bar-fill' style='width:{pct:.2f}%; background:{color};'></div></div>"
            + f"<div class='bar-pct'>{pct}%</div>"
            + "</div>"
        )

    return (
        "<div class='visual-card'>"
        "<h2>Owner workload (directional)</h2>"
        "<p><strong>Metric: denial_count (claims) for Top 10 ticket patterns.</strong></p>"
        + "".join(owner_rows)
        + "</div>"
        + "<div class='visual-card'>"
        + "<h2>Top pattern impact share</h2>"
        + "".join(impact_rows)
        + "<p><em>share of denied_amount_proxy across Top 10 ticket patterns</em></p>"
        + "</div>"
        + "<div class='visual-card'>"
        + "<h2>Evidence readiness (checklist completeness proxy)</h2>"
        + "".join(readiness_rows)
        + "<p><em>proxy from checklist item count; not an adjudication quality measure</em></p>"
        + "</div>"
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate Denials Root Cause Intelligence (RCI) brief from dbt BigQuery mart.")
    p.add_argument("--project", default="rcm-flagship")
    p.add_argument("--dataset", default="rcm")
    p.add_argument("--relation", default="mart_workqueue_claims")
    p.add_argument("--out", default="exports")
    p.add_argument("--workqueue-size", type=int, default=200)
    p.add_argument("--summary-limit", type=int, default=50)
    p.add_argument("--patterns-per-bucket", type=int, default=5)
    p.add_argument("--ticket-pack-size", type=int, default=10)
    p.add_argument("--lookback-days", type=int, default=14)
    p.add_argument("--as-of-date", default="", help="Optional YYYY-MM-DD anchor")
    p.add_argument("--dry-run-sql", action="store_true")
    p.add_argument("--determinism-check", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    source_fqn = f"{args.project}.{args.dataset}.{args.relation}"
    anchor_date = date.fromisoformat(args.as_of_date) if args.as_of_date else date.today()

    min_sql = MIN_AGING_SQL.format(source_fqn=source_fqn)
    detail_sql = DETAIL_SQL.format(source_fqn=source_fqn)

    if args.dry_run_sql:
        print(f"RCI_SOURCE={source_fqn}")
        print("-- MIN_AGING_SQL --")
        print(min_sql)
        print("-- DETAIL_SQL --")
        print(detail_sql)
        return 0

    client = bigquery.Client(project=args.project)
    min_df = _run_query(client, min_sql, [])
    min_aging_days = int(min_df.iloc[0]["min_aging_days"]) if not min_df.empty and pd.notna(min_df.iloc[0]["min_aging_days"]) else 0

    detail_df = _run_query(
        client,
        detail_sql,
        [
            bigquery.ScalarQueryParameter("anchor_date", "DATE", anchor_date.isoformat()),
            bigquery.ScalarQueryParameter("min_aging_days", "INT64", min_aging_days),
            bigquery.ScalarQueryParameter("lookback_days", "INT64", args.lookback_days),
        ],
    )
    if detail_df.empty:
        raise RuntimeError("No denied rows returned for selected window.")

    detail_df["dataset_week_key"] = pd.to_datetime(detail_df["dataset_week_key"]).dt.date
    week_keys = sorted(detail_df["dataset_week_key"].unique())
    current_week = week_keys[-1]
    current_df = detail_df[detail_df["dataset_week_key"] == current_week].copy()

    current_df["action_category"] = [
        _assign_action_category(str(a), str(p))
        for a, p in zip(current_df["next_action_text"], current_df["pattern_text"])
    ]
    current_df["owner"] = current_df["action_category"].map(OWNER_MAP).fillna("RCM analyst review")
    current_df["evidence_checklist"] = current_df["action_category"].map(EVIDENCE_MAP).fillna(EVIDENCE_MAP["OTHER_ACTION"])
    current_df["priority_component"] = current_df["denied_amount_proxy"] * current_df["preventability_weight"]

    summary_df = (
        current_df.groupby("denial_bucket", as_index=False)
        .agg(
            denied_amount_sum=("denied_amount_proxy", "sum"),
            denial_count=("claim_id", "size"),
            priority_score=("priority_component", "sum"),
        )
        .sort_values(["priority_score", "denied_amount_sum", "denial_bucket"], ascending=[False, False, True], kind="mergesort")
        .head(args.summary_limit)
        .reset_index(drop=True)
    )
    total_priority = float(summary_df["priority_score"].sum()) if not summary_df.empty else 0.0
    summary_df["share"] = summary_df["priority_score"] / total_priority if total_priority > 0 else 0.0
    summary_df["rank"] = summary_df.index + 1
    summary_df["payer_dim_status"] = "MISSING_IN_MART"
    summary_out = summary_df[
        [
            "denial_bucket",
            "denied_amount_sum",
            "denial_count",
            "priority_score",
            "share",
            "rank",
            "payer_dim_status",
        ]
    ].copy()

    pattern_grouped = (
        current_df.groupby(["denial_bucket", "pattern_text", "action_category", "owner", "evidence_checklist"], as_index=False)
        .agg(
            denied_amount_sum=("denied_amount_proxy", "sum"),
            denial_count=("claim_id", "size"),
            avg_denied=("denied_amount_proxy", "mean"),
        )
        .sort_values(["denial_bucket", "denied_amount_sum", "pattern_text"], ascending=[True, False, True], kind="mergesort")
        .reset_index(drop=True)
    )

    bucket_totals = pattern_grouped.groupby("denial_bucket", as_index=False).agg(bucket_total=("denied_amount_sum", "sum"))
    pattern_grouped = pattern_grouped.merge(bucket_totals, on="denial_bucket", how="left")
    pattern_grouped["share_within_bucket"] = pattern_grouped["denied_amount_sum"] / pattern_grouped["bucket_total"].replace(0, pd.NA)
    pattern_grouped["share_within_bucket"] = pd.to_numeric(
        pattern_grouped["share_within_bucket"], errors="coerce"
    ).fillna(0.0)

    rank_map = summary_out[["denial_bucket", "rank"]].copy()
    pattern_grouped = pattern_grouped.merge(rank_map, on="denial_bucket", how="left")
    pattern_grouped = pattern_grouped.sort_values(["rank", "denied_amount_sum", "pattern_text"], ascending=[True, False, True], kind="mergesort")
    patterns_top = pattern_grouped.groupby("denial_bucket", as_index=False, group_keys=False).head(args.patterns_per_bucket).copy()
    patterns_top = patterns_top.sort_values(["rank", "denied_amount_sum", "pattern_text"], ascending=[True, False, True], kind="mergesort")
    patterns_out = patterns_top[
        [
            "denial_bucket",
            "pattern_text",
            "action_category",
            "owner",
            "denied_amount_sum",
            "denial_count",
            "avg_denied",
            "share_within_bucket",
            "evidence_checklist",
        ]
    ].reset_index(drop=True)

    top_bucket_names = ", ".join(summary_out.head(2)["denial_bucket"].tolist()) if not summary_out.empty else "NONE"
    top2_share = float(summary_out.head(2)["share"].sum()) if not summary_out.empty else 0.0

    action_owner_df = (
        patterns_out.groupby(["action_category", "owner"], as_index=False)
        .agg(denied_amount_sum=("denied_amount_sum", "sum"), pattern_count=("pattern_text", "size"))
        .sort_values(["denied_amount_sum", "action_category"], ascending=[False, True], kind="mergesort")
    )

    evidence_df = (
        patterns_out[["action_category", "evidence_checklist"]]
        .drop_duplicates()
        .sort_values(["action_category", "evidence_checklist"], kind="mergesort")
        .reset_index(drop=True)
    )

    top_actions = action_owner_df.head(3)["action_category"].tolist()
    upstream_lines = [UPSTREAM_FIX_MAP.get(a, UPSTREAM_FIX_MAP["OTHER_ACTION"]) for a in top_actions]

    md_lines: list[str] = [
        "# Denials Root Cause Intelligence Brief v1",
        "",
        "## Impact in 90 Seconds (RCI)",
        f"- Week key: {pd.to_datetime(current_week).strftime('%Y-%m-%d')}",
        f"- Total denied proxy exposure: {_fmt_money(float(summary_out['denied_amount_sum'].sum()))}",
        f"- Top buckets: {top_bucket_names}",
        f"- Top-2 concentration: {_fmt_pct(top2_share)} of weighted priority",
        "- Use this for directional root-cause triage and evidence routing, not causal savings claims.",
        "",
        "## Top buckets + what's driving them",
    ]
    for _, row in summary_out.head(5).iterrows():
        md_lines.append(
            f"- {row['denial_bucket']}: denied {_fmt_money(float(row['denied_amount_sum']))}, "
            f"priority {_fmt_money(float(row['priority_score']))}, rank {int(row['rank'])}."
        )

    md_lines.extend([
        "",
        "## Top Patterns (within buckets)",
        "| denial_bucket | pattern_text | action_category | owner | denied_amount_sum | denial_count | share_within_bucket |",
        "|---|---|---|---|---:|---:|---:|",
    ])
    for _, row in patterns_out.iterrows():
        md_lines.append(
            f"| {_safe_md_cell(row['denial_bucket'])} | {_safe_md_cell(row['pattern_text'])} | {_safe_md_cell(row['action_category'])} | {_safe_md_cell(row['owner'])} | {_fmt_money(float(row['denied_amount_sum']))} | {int(row['denial_count'])} | {_fmt_pct(float(row['share_within_bucket']))} |"
        )

    md_lines.extend([
        "",
        "## Action categories + owners",
        "| action_category | owner | denied_amount_sum | pattern_count |",
        "|---|---|---:|---:|",
    ])
    for _, row in action_owner_df.iterrows():
        md_lines.append(
            f"| {row['action_category']} | {row['owner']} | {_fmt_money(float(row['denied_amount_sum']))} | {int(row['pattern_count'])} |"
        )

    md_lines.extend([
        "",
        "## Evidence checklist",
        "| action_category | evidence_checklist |",
        "|---|---|",
    ])
    for _, row in evidence_df.iterrows():
        md_lines.append(f"| {row['action_category']} | {row['evidence_checklist']} |")

    md_lines.extend([
        "",
        "## Upstream fixes (hypotheses)",
    ])
    for line in upstream_lines:
        md_lines.append(f"- {line}")

    md_lines.extend(
        [
            "",
            "## What to do Monday",
            "- Open `docs/denials_rci_ticket_pack_v1.html` for the Top 10 operational ticket list (owner, lever, evidence, KPI).",
            "- Route each ticket to the mapped owner and require evidence before process change.",
            "- Keep actions reversible until next comparable week confirms pattern persistence.",
        ]
    )

    md_lines.extend([
        "",
        "## Falsification / when we're wrong",
        "- If the next comparable week shifts top-bucket ranks materially, reclassify patterns before scaling interventions.",
        "- If evidence collection contradicts action category assumptions, move patterns to OTHER_ACTION and update mapping rules.",
    ])

    markdown = "\n".join(md_lines).strip() + "\n"

    ticket_candidates = pattern_grouped[
        [
            "denial_bucket",
            "pattern_text",
            "action_category",
            "owner",
            "denied_amount_sum",
            "denial_count",
            "share_within_bucket",
            "evidence_checklist",
        ]
    ].copy()
    ticket_df = _build_ticket_pack(ticket_candidates).head(args.ticket_pack_size).reset_index(drop=True)
    ticket_markdown = _ticket_pack_markdown(source_fqn, current_week, ticket_df)
    ticket_visual_html = _build_ticket_pack_visual_html(ticket_df)
    ticket_body_html = _markdown_to_html(ticket_markdown)
    ticket_html_doc = _to_html_document("Denials RCI Ticket Pack v1", ticket_body_html, ticket_visual_html)

    patterns_overall = pattern_grouped.sort_values(["denied_amount_sum", "pattern_text"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    visual_html = _build_visual_html(patterns_overall, summary_out, pattern_grouped)
    body_html = _markdown_to_html(markdown)
    html_doc = _to_html_document("Denials Root Cause Intelligence Brief v1", body_html, visual_html)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / "denials_rci_summary_v1.csv"
    patterns_path = out_dir / "denials_rci_patterns_v1.csv"
    tickets_path = out_dir / "denials_rci_tickets_v1.csv"
    md_path = docs_dir / "denials_rci_brief_v1.md"
    html_path = docs_dir / "denials_rci_brief_v1.html"
    ticket_md_path = docs_dir / "denials_rci_ticket_pack_v1.md"
    ticket_html_path = docs_dir / "denials_rci_ticket_pack_v1.html"

    summary_out.to_csv(summary_path, index=False)
    patterns_out.to_csv(patterns_path, index=False)
    ticket_df.to_csv(tickets_path, index=False)
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html_doc, encoding="utf-8")
    ticket_md_path.write_text(ticket_markdown, encoding="utf-8")
    ticket_html_path.write_text(ticket_html_doc, encoding="utf-8")

    if args.determinism_check:
        h1 = hashlib.sha256(html_path.read_bytes()).hexdigest()
        html_path.write_text(html_doc, encoding="utf-8")
        h2 = hashlib.sha256(html_path.read_bytes()).hexdigest()
        t1 = hashlib.sha256(ticket_html_path.read_bytes()).hexdigest()
        ticket_html_path.write_text(ticket_html_doc, encoding="utf-8")
        t2 = hashlib.sha256(ticket_html_path.read_bytes()).hexdigest()
        brief_match = h1 == h2
        ticket_match = t1 == t2
        print(f"DETERMINISM_HTML_SHA_FIRST={h1}")
        print(f"DETERMINISM_HTML_SHA_SECOND={h2}")
        print(f"DETERMINISM_TICKET_HTML_SHA_FIRST={t1}")
        print(f"DETERMINISM_TICKET_HTML_SHA_SECOND={t2}")
        print(f"MATCH={'TRUE' if brief_match and ticket_match else 'FALSE'}")
        if not (brief_match and ticket_match):
            raise RuntimeError("Determinism check failed: HTML hash mismatch.")

    print(f"RCI_SOURCE={source_fqn}")
    print(f"RCI_WEEK_KEY={pd.to_datetime(current_week).strftime('%Y-%m-%d')}")
    print(f"RCI_TOP_BUCKETS={top_bucket_names}")
    print(f"RCI_TOP_PATTERNS_WRITTEN={len(patterns_out)}")
    print(f"WROTE={summary_path}")
    print(f"WROTE={patterns_path}")
    print(f"WROTE={tickets_path}")
    print(f"WROTE={md_path}")
    print(f"WROTE={html_path}")
    print(f"WROTE={ticket_md_path}")
    print(f"WROTE={ticket_html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
