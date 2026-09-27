from qanuntrace.legal_reference import parse_legislative_reference as parse


def test_compound_article_and_clause():
    r = parse('البند ج من الفقرة 2 من المادة الرابعة والخمسون بعد المائتين')
    assert r is not None and (r.article, r.paragraph, r.item, r.needs_review) == (254, '2', 'ج', False)


def test_repeated_article():
    r = parse('المادة المكررة ثانياً')
    assert r is not None and r.needs_review  # no base article: never infer one
    r = parse('المادة ٥ المكررة ثانياً')
    assert r is not None and (r.article, r.repeated, r.needs_review) == (5, 2, False)


def test_ambiguous_and_unsupported_fail_closed():
    r = parse('المادة الخامسة والمادة السابعة')
    assert r is not None and r.reason == 'multiple_articles'
    r = parse('المادة البليون')
    assert r is not None and r.needs_review


def test_no_silent_inference_on_trailing_words_and_letters():
    for text in ('المادة الرابعة والخمسون بعد المائتين والمجهولة',
                 'المادة الخامسة والسابعة'):
        r = parse(text)
        assert r is not None and r.needs_review
    r = parse('المادة ٥ من نظام افتراضي')
    assert r is not None and r.article == 5 and not r.needs_review
