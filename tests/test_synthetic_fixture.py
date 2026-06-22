import pytest
from newsdom_api.synthetic import _split_vertical
from pathlib import Path

from newsdom_api.synthetic import generate_fixture


def test_generate_fixture_writes_pdf_and_truth(tmp_path: Path):
    pdf_path, truth_path = generate_fixture(tmp_path, seed=7)
    assert pdf_path.exists()
    assert truth_path.exists()


@pytest.mark.parametrize(
    "text, max_chars, expected",
    [
        ("abcdefgh", 3, ["abc", "def", "gh"]),
        ("abcdef", 3, ["abc", "def"]),
        ("a", 3, ["a"]),
        ("", 3, []),
        ("abcdef", 1, ["a", "b", "c", "d", "e", "f"]),
        ("abcdef", 10, ["abcdef"]),
    ],
)
def test_split_vertical(text: str, max_chars: int, expected: list[str]):
    assert _split_vertical(text, max_chars) == expected
