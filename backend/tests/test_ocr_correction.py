import pytest
from app.services.ocr_correction import (
    detect_ocr_errors, apply_corrections, correct_transcription,
    get_ocr_correction_summary, preprocess_for_proofing,
    OCRCorrection, OCRCorrectionResult
)


def test_detect_ocr_o_to_zero():
    """Test detection of O → 0 in octal constants"""
    text = "CA TIME1O\nTC TIME1OI\n"
    corrections = detect_ocr_errors(text)
    assert len(corrections) >= 1
    o_corrections = [c for c in corrections if "O → 0" in c.pattern_description]
    assert len(o_corrections) >= 1
    assert o_corrections[0].corrected_text == "TIME10"
    assert o_corrections[0].confidence >= 0.9


def test_detect_ocr_i_to_one():
    """Test detection of I → 1 in octal constants"""
    text = "CA TIME1I\n"
    corrections = detect_ocr_errors(text)
    i_corrections = [c for c in corrections if "I → 1" in c.pattern_description]
    assert len(i_corrections) >= 1
    assert i_corrections[0].corrected_text == "TIME11"
    assert i_corrections[0].confidence >= 0.9


def test_detect_ocr_s_to_five():
    """Test detection of S → 5 in octal constants"""
    text = "CA TIME1S\n"
    corrections = detect_ocr_errors(text)
    s_corrections = [c for c in corrections if "S → 5" in c.pattern_description]
    assert len(s_corrections) >= 1
    assert s_corrections[0].corrected_text == "TIME15"


def test_detect_ocr_z_to_two():
    """Test detection of Z → 2 in octal constants"""
    text = "CA TIME1Z\n"
    corrections = detect_ocr_errors(text)
    z_corrections = [c for c in corrections if "Z → 2" in c.pattern_description]
    assert len(z_corrections) >= 1
    assert z_corrections[0].corrected_text == "TIME12"


def test_detect_ocr_b_to_eight():
    """Test detection of B → 8 (likely decimal context)"""
    text = "CA TIME1B\n"
    corrections = detect_ocr_errors(text)
    b_corrections = [c for c in corrections if "B → 8" in c.pattern_description]
    assert len(b_corrections) >= 1


def test_detect_ocr_d_to_zero():
    """Test detection of D → 0 in octal constants"""
    text = "CA TIME1D\n"
    corrections = detect_ocr_errors(text)
    d_corrections = [c for c in corrections if "D → 0" in c.pattern_description]
    assert len(d_corrections) >= 1


def test_detect_ocr_g_to_six():
    """Test detection of G → 6 in octal constants"""
    text = "CA TIME1G\n"
    corrections = detect_ocr_errors(text)
    g_corrections = [c for c in corrections if "G → 6" in c.pattern_description]
    assert len(g_corrections) >= 1


def test_detect_ocr_q_to_nine():
    """Test detection of Q → 9 (likely decimal context)"""
    text = "CA TIME1Q\n"
    corrections = detect_ocr_errors(text)
    q_corrections = [c for c in corrections if "Q → 9" in c.pattern_description]
    assert len(q_corrections) >= 1


def test_skip_comments():
    """Test that comments are skipped"""
    text = "CA TIME10\n# This is a comment with O and I\nTC TIME1I\n"
    corrections = detect_ocr_errors(text)
    line_numbers = [c.line_number for c in corrections]
    assert 2 not in line_numbers
    assert 3 in line_numbers


def test_skip_empty_lines():
    """Test that empty lines are skipped"""
    text = "CA TIME10\n\nTC TIME1I\n"
    corrections = detect_ocr_errors(text)
    line_numbers = [c.line_number for c in corrections]
    assert 1 not in line_numbers
    assert 2 not in line_numbers
    assert 3 in line_numbers


def test_apply_corrections():
    """Test applying corrections to text"""
    text = "CA TIME1O\nTC TIME1I\n"
    corrections = detect_ocr_errors(text)
    corrected = apply_corrections(text, corrections)
    assert "TIME10" in corrected
    assert "TIME11" in corrected
    assert "TIME1O" not in corrected
    assert "TIME1I" not in corrected


def test_correct_transcription_full():
    """Test full transcription correction"""
    text = "CA TIME1O\nTC TIME1I\nCCS TIME1S\n"
    result = correct_transcription("test-program", text)
    assert result.program_id == "test-program"
    assert result.original_lines == 3
    assert result.corrections_applied >= 3
    assert "TIME10" in result.corrected_text
    assert "TIME11" in result.corrected_text
    assert "TIME15" in result.corrected_text
    assert result.overall_confidence > 0.8


def test_get_ocr_correction_summary():
    """Test OCR correction summary generation"""
    text = "CA TIME1O\nTC TIME1I\n"
    result = correct_transcription("test-program", text)
    summary = get_ocr_correction_summary(result)
    assert summary["program_id"] == "test-program"
    assert summary["total_lines"] == 2
    assert summary["corrections_found"] >= 2
    assert "pattern_breakdown" in summary
    assert summary["overall_confidence"] > 0.8


@pytest.mark.asyncio
async def test_preprocess_for_proofing():
    """Test preprocessing for proofing pipeline"""
    text = "CA TIME1O\nTC TIME1I\n"
    corrected_text, corrections = await preprocess_for_proofing(text)
    assert "TIME10" in corrected_text
    assert "TIME11" in corrected_text
    assert len(corrections) >= 2


def test_no_false_positive_on_valid_registers():
    """Test that valid AGC registers are not flagged"""
    text = "CA A\nTC Q\nCCS Z\n"
    corrections = detect_ocr_errors(text)
    assert len(corrections) == 0


def test_deduplicate_overlapping_corrections():
    """Test that overlapping corrections are deduplicated"""
    text = "CA TIME1OI\n"
    corrections = detect_ocr_errors(text)
    line_corrections = [c for c in corrections if c.line_number == 1]
    for i, c1 in enumerate(line_corrections):
        for c2 in line_corrections[i+1:]:
            assert not (c1.column_start < c2.column_end and c2.column_start < c1.column_end)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
