from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

def _fmt_date(d) -> str:
    if d is None:
        return "N/A"
    # pandas Timestamp, datetime, date all ok
    return str(getattr(d, "date", lambda: d)()).split(" ")[0] if hasattr(d, "date") else str(d).split(" ")[0]

def _ascii(s: str) -> str:
    s.encode("ascii")  # hard fail if non-ascii
    return s

@dataclass
class Receipt:
    model_as_of_date: str
    anchor_week: str
    comparator_week: str
    included_weeks: str
    window_text: str
    generated_on: str

def build_receipt(
    *,
    model_as_of_date,
    anchor_week,
    comparator_week,
    n_complete_weeks: Optional[int],
    target_complete_weeks: int = 52,
    included_weeks: str = "complete + mature only (marts flags)",
    generated_on: Optional[datetime] = None,
) -> str:
    gen = generated_on or datetime.now()
    n = n_complete_weeks
    window = f"last {n} complete weeks available (target {target_complete_weeks})" if n is not None else f"last N complete weeks available (target {target_complete_weeks})"
    lines = [
        "## Data Receipt",
        f"- Model as_of_date (from marts): {_fmt_date(model_as_of_date)}",
        f"- Anchor week: {_fmt_date(anchor_week)}",
        f"- Comparator: {_fmt_date(comparator_week)}",
        f"- Included weeks: {included_weeks}",
        f"- Window: {window}",
        f"- Generated on: {_fmt_date(gen)}",
    ]
    return _ascii("\n".join(lines))

def compute_interpretation_status(
    *,
    has_comparator: bool,
    mix_stable: Optional[bool],
    has_partial_week: Optional[bool],
    min_history_ok: bool,
) -> Dict[str, Any]:
    reasons: List[str] = []
    if not has_comparator:
        reasons.append("Comparator missing")
    if mix_stable is False:
        reasons.append("Mix stability flagged")
    if has_partial_week is True:
        reasons.append("Partial-week present (excluded from comparisons)")
    if not min_history_ok:
        reasons.append("Insufficient complete-week history for stable trending")

    status = "STABLE" if len(reasons) == 0 else "INVESTIGATE"
    reason = "All marts readiness checks passed." if status == "STABLE" else "; ".join(reasons)

    return {"status": status, "reason": reason}

def render_interpretation_block(status: str, reason: str) -> str:
    lines = [
        "## Interpretation Status",
        f"- Status: {status}",
        f"- Reason: {reason}",
        "- Action: If STABLE -> proceed to prioritization; if INVESTIGATE -> analyze drivers before queue expansion",
    ]
    return _ascii("\n".join(lines))

def load_table(name: str, offline: bool, bq_loader_fn, fixture_path: str):
    """
    name: logical table name (e.g., 'ds0', 'ds1', 'ds2', 'ds3_top25')
    offline: if True, load from CSV fixture_path
    bq_loader_fn: callable that returns a dataframe when online
    fixture_path: path to csv fixture
    """
    import pandas as pd

    if offline:
        path = fixture_path
        if not Path(path).is_absolute():
            repo_root = Path(__file__).resolve().parents[2]
            path = repo_root / path
        return pd.read_csv(path)

    return bq_loader_fn()
