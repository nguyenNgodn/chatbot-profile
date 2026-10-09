from ragchat.cache import TTLCache, normalize_query


def test_normalize_query_collapses_space_and_case():
    assert normalize_query("  Xin   Chào ") == "xin chào"


def test_ttl_cache_set_get_and_clear():
    cache = TTLCache(ttl_seconds=60)
    cache.set("k", {"ok": True})
    assert cache.get("k") == {"ok": True}
    cache.clear()
    assert cache.get("k") is None
