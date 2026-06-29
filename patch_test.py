with open("tests/test_dom_builder.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if "def test_coerce_page_number_returns_none_for_type_and_value_errors():" in line:
        new_lines.append('    assert _coerce_page_number([1, 2, 3]) is None\n')
        new_lines.append('    assert _coerce_page_number({"a": 1}) is None\n')
        new_lines.append('    assert _coerce_page_number(1) == 1\n')
        new_lines.append('    assert _coerce_page_number("2") == 2\n')

with open("tests/test_dom_builder.py", "w") as f:
    f.writelines(new_lines)
