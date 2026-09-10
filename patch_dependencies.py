import re

with open("pyproject.toml", "r") as f:
    content = f.read()

# Update httpcore2 to >=2.4.1 (or similar) or httpx2
# We need to find the vulnerable versions.
# [HIGH (security-severity=8.1)] CVE-2026-84381 uv.lock:1 - Package: httpcore2
# [HIGH (security-severity=7.5)] CVE-2026-84382 uv.lock:1 - Package: httpx2
# [MEDIUM (security-severity=5.5)] CVE-2026-84309 uv.lock:1 - Package: pypdf

# The user's memory says:
# To resolve vulnerable dependency alerts (e.g., from `trivy-fs` or similar scanners) in repositories using `uv` for package management, use the `uv lock --upgrade-package <package_name>` command to update the lockfile and remediate the CI failure. However, if your task is strictly limited to fixing exactly ONE issue, do not bundle lockfile dependency updates with other codebase fixes, as reviewers will reject it as out-of-scope. Revert the lockfile changes if necessary.
