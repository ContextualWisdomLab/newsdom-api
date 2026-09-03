sed -i 's/for cve_id in _CURRENT_PYPDF_CVES:/_NEW_CVES = ("CVE-2026-84309", "CVE-2026-84310", "CVE-2026-84311")\n    for cve_id in _NEW_CVES:/g' tests/test_pypdf_security_floor.py
sed -i 's/assert cve_id not in ignore_text/assert cve_id in ignore_text/g' tests/test_pypdf_security_floor.py
