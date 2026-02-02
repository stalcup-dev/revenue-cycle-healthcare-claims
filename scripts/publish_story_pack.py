from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    notebooks = [
        repo_root / "notebooks" / "nb01_metric_lineage_audit.ipynb",
        repo_root / "notebooks" / "nb03_exec_overview_artifact.ipynb",
        repo_root / "notebooks" / "nb04_driver_pareto_story.ipynb",
        repo_root / "notebooks" / "nb05_workqueue_story.ipynb",
    ]

    for nb in notebooks:
        cmd = [
            sys.executable,
            "-m",
            "nbconvert",
            "--execute",
            "--to",
            "notebook",
            "--inplace",
            str(nb),
            "--ExecutePreprocessor.cwd=.",
        ]
        result = subprocess.run(cmd, cwd=repo_root)
        if result.returncode != 0:
            return result.returncode

    print("PUBLISH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
