"""
Historical Scan Reference Integration for Apollo 11 AGC Transcription Verification.

Fetches and caches scan metadata from ibiblio.org Apollo scan archives.
Provides offline fallback with curated scan references for known programs.
"""

import re
import json
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
from ..core.config import settings

# Base URL for Apollo scan archives
IBIBLIO_BASE = "https://www.ibiblio.org/apollo"
SCANS_BASE = f"{IBIBLIO_BASE}/ScansForConversion/Luminary099"

def _cat(name: str, craft: str, source: str, scan_base: str, pages: dict) -> dict:
    return {"program_name": name, "craft": craft, "source": source, "scan_base": scan_base, "pages": pages}

def _page(start: int, end: int, desc: str, url: str, quality: str = "reduced") -> dict:
    return {"start_page": start, "end_page": end, "description": desc, "quality": quality, "url": url}

SCAN_CATALOG = {
    "luminary099-waitlist": _cat("WAITLIST", "LM", "Luminary099", SCANS_BASE,
        {"1117-1132": _page(1117, 1132, "WAITLIST.agc (Lines 1-564)", SCANS_BASE)}),
    "luminary099-powered_flight": _cat("POWERED_FLIGHT_SUBROUTINES", "LM", "Luminary099", SCANS_BASE,
        {"1259-1267": _page(1259, 1267, "POWERED_FLIGHT_SUBROUTINES.agc (Lines 1-447)", SCANS_BASE)}),
    "luminary099-phase_table": _cat("PHASE_TABLE_MAINTENANCE", "LM", "Luminary099", SCANS_BASE,
        {"1294-1302": _page(1294, 1302, "PHASE_TABLE_MAINTENANCE.agc (Lines 1-411)", SCANS_BASE)}),
    "luminary099-orbital_integration": _cat("ORBITAL_INTEGRATION", "LM", "Luminary099", SCANS_BASE,
        {"1227-1248": _page(1227, 1248, "ORBITAL_INTEGRATION.agc (Lines 1-977)", SCANS_BASE)}),
    "luminary099-time_free_fall": _cat("TIME_OF_FREE_FALL", "LM", "Luminary099", SCANS_BASE,
        {"1268-1283": _page(1268, 1283, "TIME_OF_FREE_FALL.agc (Lines 1-721)", SCANS_BASE)}),
    "luminary099-tjet_law": _cat("TJET_LAW", "LM", "Luminary099", SCANS_BASE,
        {"1460-1469": _page(1460, 1469, "TJET_LAW.agc (Lines 1-519)", SCANS_BASE)}),
    "comanche055-p20-p25": _cat("P20-P25", "CM", "Comanche055", f"{IBIBLIO_BASE}/listings/Comanche055",
        {"p20-p25": _page(0, 0, "P20-P25.agc listing (Comanche 055)", f"{IBIBLIO_BASE}/listings/Comanche055/P20-P25.agc.html", "html")}),
}

# Cache file for offline fallback
CACHE_DIR = Path(__file__).parent.parent.parent.parent / ".cache"
CACHE_FILE = CACHE_DIR / "scan_references.json"


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_cache() -> Dict[str, Any]:
    _ensure_cache_dir()
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_cache(data: Dict[str, Any]):
    _ensure_cache_dir()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


async def fetch_scan_metadata(program_id: str) -> Dict[str, Any]:
    """
    Fetch scan metadata for a program from ibiblio.org.
    Uses catalog for known programs, falls back to HTTP discovery for unknown.
    """
    catalog_entry = SCAN_CATALOG.get(program_id)
    if catalog_entry:
        # Return cached/known data immediately
        result = {
            "program_id": program_id,
            "program_name": catalog_entry["program_name"],
            "craft": catalog_entry["craft"],
            "source": catalog_entry["source"],
            "scan_base_url": catalog_entry["scan_base"],
            "pages": catalog_entry["pages"],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source_type": "catalog"
        }
        # Cache it
        _save_cache({program_id: result})
        return result

    # For unknown programs, try to discover from ibiblio
    cache = _load_cache()
    if program_id in cache:
        cached = cache[program_id].copy()
        cached["source_type"] = "cache"
        return cached

    # Attempt HTTP discovery
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try both Luminary and Comanche listings
            for craft in ["Luminary099", "Comanche055"]:
                url = f"{IBIBLIO_BASE}/listings/{craft}/{program_id}.agc.html"
                try:
                    resp = await client.head(url, follow_redirects=True)
                    if resp.status_code == 200:
                        result = {
                            "program_id": program_id,
                            "program_name": program_id.replace("_", "-").upper(),
                            "craft": "LM" if craft == "Luminary099" else "CM",
                            "source": craft,
                            "scan_base_url": f"{IBIBLIO_BASE}/listings/{craft}",
                            "pages": {
                                "listing": {
                                    "start_page": 0,
                                    "end_page": 0,
                                    "description": f"{program_id} listing ({craft})",
                                    "quality": "html",
                                    "url": url
                                }
                            },
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                            "source_type": "discovered"
                        }
                        _save_cache({program_id: result})
                        return result
                except httpx.HTTPError:
                    continue
    except Exception:
        pass

    # Fallback: return minimal structure
    return {
        "program_id": program_id,
        "program_name": program_id.replace("_", "-").upper(),
        "craft": "UNKNOWN",
        "source": "UNKNOWN",
        "scan_base_url": IBIBLIO_BASE,
        "pages": {},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "fallback",
        "error": "No scan reference found in catalog or via discovery"
    }


def get_scan_pages_for_program(program_id: str) -> List[Dict[str, Any]]:
    """Get list of scan page ranges for a program (sync, from catalog/cache)."""
    metadata = fetch_scan_metadata_sync(program_id)
    pages = []
    for key, page_info in metadata.get("pages", {}).items():
        pages.append({
            "range_key": key,
            "start_page": page_info.get("start_page", 0),
            "end_page": page_info.get("end_page", 0),
            "description": page_info.get("description", ""),
            "quality": page_info.get("quality", "unknown"),
            "url": page_info.get("url", "")
        })
    return pages


def fetch_scan_metadata_sync(program_id: str) -> Dict[str, Any]:
    """Synchronous version for non-async contexts."""
    catalog_entry = SCAN_CATALOG.get(program_id)
    if catalog_entry:
        return {
            "program_id": program_id,
            "program_name": catalog_entry["program_name"],
            "craft": catalog_entry["craft"],
            "source": catalog_entry["source"],
            "scan_base_url": catalog_entry["scan_base"],
            "pages": catalog_entry["pages"],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source_type": "catalog"
        }

    cache = _load_cache()
    if program_id in cache:
        cached = cache[program_id].copy()
        cached["source_type"] = "cache"
        return cached

    return {
        "program_id": program_id,
        "program_name": program_id.replace("_", "-").upper(),
        "craft": "UNKNOWN",
        "source": "UNKNOWN",
        "scan_base_url": IBIBLIO_BASE,
        "pages": {},
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "fallback",
        "error": "No scan reference found"
    }


def get_scan_url_for_line(program_id: str, line_number: int) -> Optional[str]:
    """
    Get the scan page URL that corresponds to a given line number.
    Returns the best matching page range URL.
    """
    metadata = fetch_scan_metadata_sync(program_id)
    for page_key, page_info in metadata.get("pages", {}).items():
        start = page_info.get("start_page", 0)
        end = page_info.get("end_page", 0)
        # Rough heuristic: ~40 lines per page for AGC listings
        if start > 0 and end > 0:
            # We don't have exact line-to-page mapping, but can estimate
            # For now return the first matching page range
            return page_info.get("url")
    return None


def list_all_known_programs() -> List[Dict[str, Any]]:
    """List all programs with known scan references."""
    return [
        {
            "program_id": pid,
            "program_name": info["program_name"],
            "craft": info["craft"],
            "source": info["source"],
            "page_ranges": list(info["pages"].keys())
        }
        for pid, info in SCAN_CATALOG.items()
    ]


# Line-to-page mapping for specific programs (approximate)
# Based on typical AGC listing density (~40-45 lines per scan page)
LINES_PER_PAGE = 42


def estimate_page_for_line(program_id: str, line_number: int) -> Optional[int]:
    """Estimate which scan page a line number falls on."""
    metadata = fetch_scan_metadata_sync(program_id)
    for page_key, page_info in metadata.get("pages", {}).items():
        start = page_info.get("start_page", 0)
        end = page_info.get("end_page", 0)
        if start > 0 and end > 0:
            # Estimate: each page ~42 lines
            estimated_start_line = (start - metadata["pages"][list(metadata["pages"].keys())[0]]["start_page"]) * LINES_PER_PAGE + 1
            estimated_end_line = estimated_start_line + (end - start + 1) * LINES_PER_PAGE
            if estimated_start_line <= line_number <= estimated_end_line:
                return start + (line_number - estimated_start_line) // LINES_PER_PAGE
    return None


def get_scan_reference_for_discrepancy(program_id: str, line_number: int) -> Dict[str, Any]:
    """
    Get scan reference information for a specific discrepancy line.
    Returns page estimate and URL for verification.
    """
    metadata = fetch_scan_metadata_sync(program_id)
    estimated_page = estimate_page_for_line(program_id, line_number)
    page_url = get_scan_url_for_line(program_id, line_number)

    return {
        "program_id": program_id,
        "line_number": line_number,
        "estimated_scan_page": estimated_page,
        "scan_url": page_url,
        "scan_base_url": metadata.get("scan_base_url"),
        "source_type": metadata.get("source_type"),
        "note": "Page estimates are approximate; consult scan directly for exact verification."
    }
