def test_parse_chunk_size_is_1MB():
    from newsdom_api.main import UPLOAD_READ_CHUNK_SIZE_BYTES
    assert UPLOAD_READ_CHUNK_SIZE_BYTES == 1024 * 1024
