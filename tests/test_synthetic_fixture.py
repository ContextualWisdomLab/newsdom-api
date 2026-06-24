from pathlib import Path

from newsdom_api.synthetic import generate_fixture


def test_generate_fixture_writes_pdf_and_truth(tmp_path: Path):
    pdf_path, truth_path = generate_fixture(tmp_path, seed=7)
    assert pdf_path.exists()
    assert truth_path.exists()
