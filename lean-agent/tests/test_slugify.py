from lean_agent.slugify import slugify_idea


def test_basic_phrase():
    assert slugify_idea("AI invoice follow-ups") == "ai-invoice-follow-ups"


def test_strips_quotes_and_punctuation():
    assert (
        slugify_idea("'Pay what you want' for first 3 months!")
        == "pay-what-you-want-for-first-3-months"
    )


def test_collapses_spaces():
    assert slugify_idea("hello   world\n\nfoo") == "hello-world-foo"


def test_truncates_long_input_to_first_8_words():
    text = "one two three four five six seven eight nine ten"
    assert slugify_idea(text) == "one-two-three-four-five-six-seven-eight"


def test_strips_unicode_to_ascii():
    assert slugify_idea("café société") == "cafe-societe"


def test_collapses_double_hyphens_and_emdash():
    assert slugify_idea("AI invoice -- follow-ups!") == "ai-invoice-follow-ups"
    assert slugify_idea("AI invoice — follow-ups") == "ai-invoice-follow-ups"


def test_returns_empty_string_when_input_has_no_ascii_word_chars():
    assert slugify_idea("") == ""
    assert slugify_idea("   ") == ""
    assert slugify_idea("!!!") == ""
    assert slugify_idea("日本語") == ""


def test_pure_hyphens_collapse_to_empty():
    # Was previously "---"; now correctly empty since '-' is a separator.
    assert slugify_idea("---") == ""
