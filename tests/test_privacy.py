import pytest

from qanuntrace.privacy import SensitiveSpan, redact, safe_model_payload


def test_redaction_bounded_examples():
    original = 'راسل a@example.org وهاتف 0501234567، الهوية ١٢٣٤٥٦٧٨٩٠، سجل تجاري 1012345678'
    result = redact(original)
    assert 'a@example.org' not in result.text
    assert '0501234567' not in result.text
    assert '١٢٣٤٥٦٧٨٩٠' not in result.text
    assert '1012345678' not in result.text
    assert result.needs_review
    assert len(result.spans) == 4


def test_names_are_not_auto_detected_and_remote_transfer_requires_review():
    with pytest.raises(PermissionError):
        safe_model_payload('أحمد وقع العقد')
    assert 'أحمد' in safe_model_payload('أحمد وقع العقد', reviewed=True)


def test_custom_spans_and_overlap_rejected():
    text = 'اسم أحمد'
    assert 'أحمد' not in redact(text, lambda _: (SensitiveSpan(4, 8, 'custom'),)).text
    with pytest.raises(ValueError):
        redact(text, lambda _: (SensitiveSpan(0, 6, 'custom'), SensitiveSpan(4, 8, 'custom')))
