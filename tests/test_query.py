from qanuntrace.query import parse_query


def test_noisy_article_forms_and_original_preserved():
    aliases = {'نظام العمل':'labor'}
    for text in ('المادة الخامسة من نظام العمل','مادة ٥ نظام العمل','م5 نظام العمل',
                 'article 5 نظام العمل'):
        parsed = parse_query(text,aliases)
        assert parsed.original == text
        assert parsed.article_refs == ('5',)
        assert parsed.instrument_ids == ('labor',)
        assert parsed.clarification is None

def test_ambiguity_is_not_guessed():
    parsed = parse_query('مادة ٥ و المادة ٦',{})
    assert parsed.clarification and parsed.article_refs == ('5','6')
    assert parse_query('مادة 5',{}).clarification
    assert parse_query('').clarification
