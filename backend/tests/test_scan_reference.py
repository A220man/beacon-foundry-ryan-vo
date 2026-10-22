import pytest
from app.services.scan_reference import (
    fetch_scan_metadata, fetch_scan_metadata_sync,
    get_scan_pages_for_program, get_scan_reference_for_discrepancy,
    list_all_known_programs, estimate_page_for_line,
    get_scan_url_for_line, SCAN_CATALOG
)


@pytest.mark.asyncio
async def test_fetch_known_program_metadata():
    """Test fetching metadata for known programs from catalog"""
    # Test Luminary WAITLIST
    meta = await fetch_scan_metadata("luminary099-waitlist")
    assert meta["program_id"] == "luminary099-waitlist"
    assert meta["program_name"] == "WAITLIST"
    assert meta["craft"] == "LM"
    assert meta["source"] == "Luminary099"
    assert meta["source_type"] == "catalog"
    assert "pages" in meta
    assert len(meta["pages"]) > 0
    assert "1117-1132" in meta["pages"]

    # Test Luminary POWERED_FLIGHT
    meta = await fetch_scan_metadata("luminary099-powered_flight")
    assert meta["program_name"] == "POWERED_FLIGHT_SUBROUTINES"
    assert meta["craft"] == "LM"

    # Test Comanche P20-P25
    meta = await fetch_scan_metadata("comanche055-p20-p25")
    assert meta["program_name"] == "P20-P25"
    assert meta["craft"] == "CM"


@pytest.mark.asyncio
async def test_fetch_unknown_program_fallback():
    """Test fallback behavior for unknown programs"""
    meta = await fetch_scan_metadata("unknown-program-xyz")
    assert meta["program_id"] == "unknown-program-xyz"
    assert meta["source_type"] == "fallback"
    assert "error" in meta


def test_fetch_scan_metadata_sync():
    """Test synchronous version of metadata fetch"""
    meta = fetch_scan_metadata_sync("luminary099-waitlist")
    assert meta["program_id"] == "luminary099-waitlist"
    assert meta["source_type"] == "catalog"

    # Test cache fallback (should be same as catalog for known programs)
    meta2 = fetch_scan_metadata_sync("luminary099-waitlist")
    assert meta2["program_name"] == "WAITLIST"


def test_get_scan_pages_for_program():
    """Test getting scan pages list for a program"""
    pages = get_scan_pages_for_program("luminary099-waitlist")
    assert len(pages) > 0
    page = pages[0]
    assert "range_key" in page
    assert "start_page" in page
    assert "end_page" in page
    assert "description" in page
    assert "quality" in page
    assert "url" in page
    assert page["start_page"] == 1117
    assert page["end_page"] == 1132


def test_get_scan_pages_unknown_program():
    """Test getting pages for unknown program returns empty list"""
    pages = get_scan_pages_for_program("unknown-xyz")
    assert pages == []


def test_get_scan_url_for_line():
    """Test getting scan URL for a specific line"""
    url = get_scan_url_for_line("luminary099-waitlist", 100)
    assert url is not None
    assert "ibiblio.org" in url

    # Unknown program
    url = get_scan_url_for_line("unknown-xyz", 100)
    assert url is None


def test_estimate_page_for_line():
    """Test page estimation for line numbers"""
    # For WAITLIST (pages 1117-1132, ~42 lines per page)
    page = estimate_page_for_line("luminary099-waitlist", 1)
    assert page is not None
    assert page >= 1117
    assert page <= 1132

    # Mid-range line
    page = estimate_page_for_line("luminary099-waitlist", 280)
    assert page is not None
    assert page >= 1117
    assert page <= 1132

    # Unknown program
    page = estimate_page_for_line("unknown-xyz", 100)
    assert page is None


def test_get_scan_reference_for_discrepancy():
    """Test getting scan reference for a discrepancy line"""
    ref = get_scan_reference_for_discrepancy("luminary099-waitlist", 100)
    assert ref["program_id"] == "luminary099-waitlist"
    assert ref["line_number"] == 100
    assert "estimated_scan_page" in ref
    assert "scan_url" in ref
    assert "scan_base_url" in ref
    assert "source_type" in ref
    assert "note" in ref
    assert "ibiblio.org" in ref["scan_base_url"]


def test_list_all_known_programs():
    """Test listing all known programs with scan references"""
    programs = list_all_known_programs()
    assert len(programs) > 0

    # Check expected programs exist
    program_ids = {p["program_id"] for p in programs}
    assert "luminary099-waitlist" in program_ids
    assert "luminary099-powered_flight" in program_ids
    assert "luminary099-phase_table" in program_ids
    assert "luminary099-orbital_integration" in program_ids
    assert "luminary099-time_free_fall" in program_ids
    assert "luminary099-tjet_law" in program_ids
    assert "comanche055-p20-p25" in program_ids

    # Check structure
    for p in programs:
        assert "program_id" in p
        assert "program_name" in p
        assert "craft" in p
        assert "source" in p
        assert "page_ranges" in p
        assert isinstance(p["page_ranges"], list)


def test_scan_catalog_completeness():
    """Test that SCAN_CATALOG contains expected entries based on GitHub issues"""
    # Issues referenced: #651 (WAITLIST), #624 (POWERED_FLIGHT), #620 (PHASE_TABLE),
    # #609 (ORBITAL_INTEGRATION), #647 (TIME_OF_FREE_FALL), #648 (TJET_LAW), #38 (P20-P25)
    expected = {
        "luminary099-waitlist",
        "luminary099-powered_flight",
        "luminary099-phase_table",
        "luminary099-orbital_integration",
        "luminary099-time_free_fall",
        "luminary099-tjet_law",
        "comanche055-p20-p25"
    }
    assert set(SCAN_CATALOG.keys()) == expected


def test_page_quality_and_urls():
    """Test that catalog entries have valid quality ratings and URLs"""
    for program_id, info in SCAN_CATALOG.items():
        for page_key, page_info in info["pages"].items():
            assert page_info["quality"] in ["reduced", "html", "unknown"]
            assert page_info["url"].startswith("http")
            assert "ibiblio.org" in page_info["url"]
            assert "description" in page_info
            assert len(page_info["description"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])