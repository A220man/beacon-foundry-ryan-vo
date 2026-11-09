"""
AGC Transcription OCR Error Detection & Correction Service

Detects and corrects common OCR transcription artifacts in AGC assembly source:
- O/0 confusion (letter O vs digit zero)
- I/1 confusion (letter I vs digit one)  
- S/5 confusion (letter S vs digit five)
- B/8 confusion (letter B vs digit eight)
- Z/2 confusion (letter Z vs digit two)
- D/0 confusion (letter D vs digit zero)
- G/6 confusion (letter G vs digit six)
- Q/9 confusion (letter Q vs digit nine)

Integrates with proofing pipeline for automated pre-processing.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from ..models.schemas import AGCInstruction


# Common OCR confusion patterns for AGC octal/register notation
# AGC register names are alphanumeric (e.g., TIME1, TIME2, CADR, etc.)
# We match alphanumeric sequences where the confusion char is the LAST character
OCR_CONFUSION_PATTERNS = [
    # (pattern, replacement, description, confidence)
    # Match confusion characters at end of alphanumeric word
    (r'\b([A-Z0-9]+)O\b', r'\g<1>0', "O → 0 at end of register", 0.90),
    (r'\b([A-Z0-9]+)I\b', r'\g<1>1', "I → 1 at end of register", 0.90),
    (r'\b([A-Z0-9]+)S\b', r'\g<1>5', "S → 5 at end of register", 0.88),
    (r'\b([A-Z0-9]+)Z\b', r'\g<1>2', "Z → 2 at end of register", 0.88),
    (r'\b([A-Z0-9]+)B\b', r'\g<1>8', "B → 8 at end of register", 0.85),
    (r'\b([A-Z0-9]+)D\b', r'\g<1>0', "D → 0 at end of register", 0.87),
    (r'\b([A-Z0-9]+)G\b', r'\g<1>6', "G → 6 at end of register", 0.87),
    (r'\b([A-Z0-9]+)Q\b', r'\g<1>9', "Q → 9 at end of register", 0.85),
]


# Valid AGC register names for context validation
VALID_AGC_REGISTERS = {
    "A", "L", "Q", "Z", "BB", "CYR", "CYL", "SR", "CYRIGHT", "CYLEFT",
    "EDOP", "EXTEND", "OV", "OVF", "TIME1", "TIME2", "TIME3", "TIME4",
    "TIME5", "TIME6", "WAITLIST", "DSRUPT", "RUPT", "INT", "INST",
    "PNTRSAV", "BRUPT", "ARUPT", "CHANSAV", "CHANLST", "PRIO", "PRIORITY",
    "UPRUPT", "DNTRUPT", "SIGOVF", "FUTRUPT", "VAC5STOR", "VACAREA",
    "CADR", "CADR2", "INHINT", "RELINT", "EXTEND", "NOOP", "TC", "TCF",
    "CCS", "DAS", "LXCH", "INCR", "ADS", "CA", "CS", "INDEX", "XCH",
    "DXCH", "TS", "AD", "MASK", "READ", "WRITE", "RAND", "WAND", "ROR",
    "WOR", "RXOR", "EDOP", "MP", "DV", "BZF", "MSU", "QXCH", "AUG",
    "DIM", "DTCB", "DTCF", "OVSK", "RETURN", "CAF", "VLOAD", "STODL",
    "BOV", "RTB", "STORE", "SUBCALL", "UNIT", "SETLOC", "BANK", "COUNT",
    "COUNT*", "BLOCK", "EBANK", "SBANK", "2CADR", "EQUALS", "DEC", "OCT",
    "ERASE", "BBCON", "BBCON", "RESUME", "WAIT", "LONG", "SHORT",
}


@dataclass
class OCRCorrection:
    """Single OCR correction suggestion"""
    original_text: str
    corrected_text: str
    line_number: int
    column_start: int
    column_end: int
    pattern_description: str
    confidence: float
    context: str  # surrounding text for review


@dataclass
class OCRCorrectionResult:
    """Result of OCR correction analysis"""
    program_id: str
    original_lines: int
    corrections: List[OCRCorrection]
    corrected_text: str
    overall_confidence: float
    corrections_applied: int


def detect_ocr_errors(text: str) -> List[OCRCorrection]:
    """
    Scan text for common OCR transcription errors in AGC source.
    Returns list of corrections with confidence scores.
    """
    corrections: List[OCRCorrection] = []
    lines = text.splitlines()
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#') or not line.strip():
            continue
            
        # Apply each confusion pattern
        for pattern, replacement, description, confidence in OCR_CONFUSION_PATTERNS:
            for match in re.finditer(pattern, line):
                original = match.group(0)
                corrected = re.sub(pattern, replacement, original)
                
                # Skip if no actual change
                if original == corrected:
                    continue
                    
                # Validate correction makes sense in context
                if not _is_valid_correction(original, corrected, line, match.start(), match.end()):
                    continue
                
                corrections.append(OCRCorrection(
                    original_text=original,
                    corrected_text=corrected,
                    line_number=line_num,
                    column_start=match.start(),
                    column_end=match.end(),
                    pattern_description=description,
                    confidence=confidence,
                    context=_get_context(line, match.start(), match.end())
                ))
    
    # Deduplicate overlapping corrections (keep highest confidence)
    corrections = _deduplicate_corrections(corrections)
    
    return corrections


def _is_valid_correction(original: str, corrected: str, line: str, start: int, end: int) -> bool:
    """Validate that a correction is contextually appropriate for AGC source."""
    # Skip if correction creates invalid octal (>7 digits)
    if re.search(r'[89]', corrected):
        # Check if we're in a decimal context (comments, DECs, etc.)
        # For now, allow it but lower confidence
        pass
    
    # Don't correct inside string literals or comments (already handled)
    # Don't correct known valid register names that happen to match
    if original in VALID_AGC_REGISTERS:
        return False
        
    return True


def _get_context(line: str, start: int, end: int, window: int = 20) -> str:
    """Get surrounding context for a correction."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(line), end + window)
    context = line[ctx_start:ctx_end]
    if ctx_start > 0:
        context = "..." + context
    if ctx_end < len(line):
        context = context + "..."
    return context


def _deduplicate_corrections(corrections: List[OCRCorrection]) -> List[OCRCorrection]:
    """Remove overlapping corrections, keeping highest confidence."""
    if not corrections:
        return []
    
    # Sort by line, then column, then confidence descending
    corrections.sort(key=lambda c: (c.line_number, c.column_start, -c.confidence))
    
    result = []
    last = None
    for corr in corrections:
        if last and corr.line_number == last.line_number:
            # Check for overlap
            if corr.column_start < last.column_end:
                # Overlapping - keep the higher confidence one (already sorted)
                continue
        result.append(corr)
        last = corr
    
    return result


def apply_corrections(text: str, corrections: List[OCRCorrection]) -> str:
    """Apply corrections to text, returning corrected version."""
    if not corrections:
        return text
    
    lines = text.splitlines(keepends=True)
    # Apply corrections line by line, from end to start to preserve positions
    corrections_by_line: Dict[int, List[OCRCorrection]] = {}
    for c in corrections:
        corrections_by_line.setdefault(c.line_number - 1, []).append(c)
    
    for line_idx, line_corrections in corrections_by_line.items():
        if line_idx >= len(lines):
            continue
        line = lines[line_idx]
        # Sort by column descending to apply from end
        line_corrections.sort(key=lambda c: -c.column_start)
        for corr in line_corrections:
            if corr.column_start < len(line) and corr.column_end <= len(line):
                line = line[:corr.column_start] + corr.corrected_text + line[corr.column_end:]
        lines[line_idx] = line
    
    return "".join(lines)


def correct_transcription(program_id: str, transcription_text: str) -> OCRCorrectionResult:
    """
    Main entry point: detect and correct OCR errors in AGC transcription.
    Returns full correction result with corrected text and confidence scores.
    """
    corrections = detect_ocr_errors(transcription_text)
    corrected_text = apply_corrections(transcription_text, corrections)
    
    # Calculate overall confidence
    if corrections:
        overall_confidence = sum(c.confidence for c in corrections) / len(corrections)
    else:
        overall_confidence = 1.0
    
    return OCRCorrectionResult(
        program_id=program_id,
        original_lines=len(transcription_text.splitlines()),
        corrections=corrections,
        corrected_text=corrected_text,
        overall_confidence=round(overall_confidence, 3),
        corrections_applied=len(corrections)
    )


def get_ocr_correction_summary(result: OCRCorrectionResult) -> Dict[str, Any]:
    """Generate summary statistics for OCR correction result."""
    pattern_counts: Dict[str, int] = {}
    for c in result.corrections:
        pattern_counts[c.pattern_description] = pattern_counts.get(c.pattern_description, 0) + 1
    
    return {
        "program_id": result.program_id,
        "total_lines": result.original_lines,
        "corrections_found": result.corrections_applied,
        "overall_confidence": result.overall_confidence,
        "pattern_breakdown": pattern_counts,
        "corrected_text_preview": result.corrected_text[:500] + ("..." if len(result.corrected_text) > 500 else "")
    }


def preprocess_for_proofing(transcription_text: str) -> Tuple[str, List[OCRCorrection]]:
    """
    Preprocess transcription for proofing pipeline.
    Returns corrected text and list of corrections applied.
    Can be used as automated pre-processing step before proof_transcription().
    """
    result = correct_transcription("unknown", transcription_text)
    return result.corrected_text, result.corrections
