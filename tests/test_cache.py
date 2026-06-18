from addchin import cache


def test_lookup_hit():
    entry = cache.lookup("朋友")
    assert entry is not None
    assert set(entry) == {"meaning", "pos", "sentence", "sentence_meaning"}


def test_lookup_miss():
    assert cache.lookup("没有这个词xyz") is None


def test_lists():
    assert "hsk1" in cache.available_lists()
    words = cache.read_list("hsk1")
    assert "朋友" in words
