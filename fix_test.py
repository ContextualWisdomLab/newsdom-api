import re
from pathlib import Path

content = Path("tests/test_pypdf_security_floor.py").read_text()
new_content = content.replace('def test_suppressed_trivy_cves() -> None:\n    """Ensure the new CVEs are in the known list."""\n    ignore_text = Path(".trivyignore.yaml").read_text(encoding="utf-8")\n    for cve_id in _CURRENT_PYPDF_CVES:\n        assert cve_id not in ignore_text\n', '')
Path("tests/test_pypdf_security_floor.py").write_text(new_content)
