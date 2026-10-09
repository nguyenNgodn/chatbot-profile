from ragchat.identity import normalize_email


def test_normalize_email_trims_and_lowercases():
    assert normalize_email("  Ada@Example.COM ") == "ada@example.com"
