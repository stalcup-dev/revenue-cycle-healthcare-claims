from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / ".tmp" / "nbconvert_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    notebooks = [
        repo_root / "notebooks" / "nb01_metric_lineage_audit.ipynb",
        repo_root / "notebooks" / "nb03_exec_overview_artifact.ipynb",
        repo_root / "notebooks" / "nb04_driver_pareto_story.ipynb",
        repo_root / "notebooks" / "nb05_workqueue_story.ipynb",
    ]

    for nb in notebooks:
        out_name = f"{nb.stem}__executed.ipynb"
        cmd = [
            sys.executable,
            "-m",
            "nbconvert",
            "--execute",
            "--to",
            "notebook",
            "--output-dir",
            str(out_dir),
            "--output",
            out_name,
            str(nb),
        ]
        subprocess.run(cmd, cwd=repo_root, check=True)

    print("PUBLISH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
