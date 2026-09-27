"""Keep the documented quickstart runnable and its output stable."""
import subprocess
import sys
from pathlib import Path


def test_quickstart_matches_readme():
    root = Path(__file__).resolve().parents[1]
    example = (root / "examples" / "quickstart.py").read_text(encoding="utf-8").rstrip()
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert f"```python\n{example}\n```" in readme
    completed = subprocess.run(
        [sys.executable, str(root / "examples" / "quickstart.py")],
        capture_output=True, text=True, check=True, cwd=root,
    )
    assert completed.stdout == (
        'verified_quote\n[sample-1] "لا يجوز تغيير النص التجريبي." (fixture:local)\n'
    )
