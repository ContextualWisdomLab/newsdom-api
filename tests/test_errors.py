from newsdom_api.errors import MineruRuntimeUnavailableError, MineruIncompleteOutputError

def test_mineru_runtime_unavailable_error_initialization():
    """Ensure MineruRuntimeUnavailableError initializes correctly."""
    error = MineruRuntimeUnavailableError(
        returncode=1,
        stdout="stdout text",
        stderr="stderr text"
    )
    assert error.returncode == 1
    assert error.stdout == "stdout text"
    assert error.stderr == "stderr text"
    assert str(error) == "MinerU runtime unavailable"

def test_mineru_incomplete_output_error_initialization():
    """Ensure MineruIncompleteOutputError initializes correctly."""
    error = MineruIncompleteOutputError()
    assert str(error) == "MinerU output was incomplete"
