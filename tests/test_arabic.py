import pytest

from qanuntrace.arabic import gulf_search_key, number_word, parse_date


def test_gulf_query_and_numbers():
    assert gulf_search_key('وش حكم المادة؟').startswith('ما حكم')
    for t in ('خامسة','الخامسة','٥','۵','5'):
        expected = None if t=='خامسة' else 5
        assert number_word(t)==expected
    assert number_word('خمسة وعشرين')==25
    assert number_word('مئة وواحد') is None

def test_calendar_detection():
    assert parse_date('٢٠٢٦/٩/٢٧م').iso_gregorian=='2026-09-27'
    with pytest.raises(ValueError): parse_date('1445/3/12')
    with pytest.raises(ValueError): parse_date('2026/13/27م')
