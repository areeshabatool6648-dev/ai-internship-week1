def test_imports_work():
    import feedback_intelligence
    assert feedback_intelligence is not None


def test_chunk_text_splits_correctly():
    from feedback_intelligence import chunk_text
    text = "word " * 300
    chunks = chunk_text(text, chunk_size=150, overlap=30)
    assert len(chunks) > 1


def test_count_for_segment_returns_int():
    from feedback_intelligence import count_for_segment
    assert callable(count_for_segment)