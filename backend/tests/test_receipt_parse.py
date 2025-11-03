from app.services.ocr_service import parse_receipt_text


def test_parse_receipt_text_extracts_amount_and_date():
    text = """
    MY CAFE
    Date: 2024-12-31
    TOTAL $12.50
    Thank you!
    """
    parsed = parse_receipt_text(text)
    assert parsed['merchant'] == 'MY CAFE'
    assert parsed['total_amount'] == 12.50
    assert parsed['date'] == '2024-12-31'


