"""Unit tests for the eTender HTTP fetcher."""

from unittest.mock import MagicMock, patch

from src.fetcher import ETenderFetcher


def test_parse_tender_valid_row():
    """Verify parsing a valid raw API dictionary row."""
    fetcher = ETenderFetcher()
    mock_row = {
        "id": 9999,
        "tender_No": "A-EE 12-2026",
        "organ_of_State": "City of Ekurhuleni",
        "province": "Gauteng",
        "category": "Supplies",
        "description": "Appointment of contractors for highmast lighting.",
        "closing_Date": "2026-12-08T10:00:00",
        "date_Published": "2026-10-23T00:00:00",
        "contactPerson": "Ronald Ndou",
        "email": "Ronald.Ndou@ekurhuleni.gov.za",
        "telephone": "011-999-0291",
        "supportDocument": [
            {
                "supportDocumentID": "doc-uuid-1",
                "fileName": "A-EE 12-2026 FINAL BID DOCUMENT.pdf",
                "extension": ".pdf",
            }
        ],
    }

    tender = fetcher._parse_tender(mock_row)
    assert tender is not None
    assert tender.tender_no == "A-EE 12-2026"
    assert tender.organ_of_state == "City of Ekurhuleni"
    assert tender.contact_email == "Ronald.Ndou@ekurhuleni.gov.za"
    assert len(tender.documents) == 1
    assert tender.documents[0].file_name == "A-EE 12-2026 FINAL BID DOCUMENT.pdf"


@patch("requests.get")
def test_fetch_active_tenders_mocked(mock_get):
    """Verify pagination and response parsing using mocked HTTP."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "recordsTotal": 1,
        "data": [
            {
                "id": 1,
                "tender_No": "TEST-01",
                "organ_of_State": "Test Organ",
                "description": "Test description",
            }
        ],
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    fetcher = ETenderFetcher()
    results = fetcher.fetch_active_tenders(max_records=1)

    assert len(results) == 1
    assert results[0].tender_no == "TEST-01"
