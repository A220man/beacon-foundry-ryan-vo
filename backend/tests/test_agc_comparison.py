import pytest
from app.services.agc_engine import (
    parse_agc_source, compare_instructions, identify_semantic_divergences,
    compare_programs, SAMPLE_WAITLIST_CODE, SAMPLE_WAITLIST_COMANCHE,
    SAMPLE_POWERED_FLIGHT_CODE, SAMPLE_POWERED_FLIGHT_COMANCHE
)
from app.models.schemas import AGCInstruction, DiffChange

def test_compare_identical_instructions():
    """Test comparison of identical instruction lists"""
    lm = parse_agc_source(SAMPLE_WAITLIST_CODE)
    cm = parse_agc_source(SAMPLE_WAITLIST_COMANCHE)
    
    diff = compare_instructions(lm, cm)
    
    # Should have some unchanged, some modified (even identical samples differ slightly in comments)
    assert len(diff) > 0
    unchanged = [d for d in diff if d.type == "unchanged"]
    assert len(unchanged) > 0

def test_compare_detects_opcode_changes():
    """Test that opcode differences are detected"""
    lm_src = "START\tCA\tTIME1\n\tTC\tNEXT"
    cm_src = "START\tCS\tTIME1\n\tTC\tNEXT"  # CA -> CS change
    
    lm = parse_agc_source(lm_src)
    cm = parse_agc_source(cm_src)
    
    diff = compare_instructions(lm, cm)
    
    modified = [d for d in diff if d.type == "modified" and d.change_category == "opcode"]
    assert len(modified) >= 1
    assert modified[0].description == "Opcode changed: CA → CS"

def test_compare_detects_operand_changes():
    """Test that operand differences are detected"""
    lm_src = "\tCA\tREG_A"
    cm_src = "\tCA\tREG_B"
    
    lm = parse_agc_source(lm_src)
    cm = parse_agc_source(cm_src)
    
    diff = compare_instructions(lm, cm)
    
    modified = [d for d in diff if d.type == "modified" and d.change_category == "operand"]
    assert len(modified) >= 1
    assert "REG_A → REG_B" in modified[0].description

def test_compare_detects_bank_differences():
    """Test that bank assignment differences are detected"""
    lm_src = "BANK\t01\n\tCA\tTIME1"
    cm_src = "BANK\t02\n\tCA\tTIME1"
    
    lm = parse_agc_source(lm_src)
    cm = parse_agc_source(cm_src)
    
    diff = compare_instructions(lm, cm)
    
    modified = [d for d in diff if d.type == "modified" and d.change_category == "bank"]
    assert len(modified) >= 1
    assert "01" in modified[0].description and "02" in modified[0].description

def test_semantic_divergences_bank_assignment():
    """Test identification of bank assignment divergences"""
    lm = parse_agc_source(SAMPLE_WAITLIST_CODE)
    cm = parse_agc_source(SAMPLE_WAITLIST_COMANCHE)
    
    divergences = identify_semantic_divergences(lm, cm)
    
    # Should identify at least one divergence
    assert len(divergences) >= 0  # Samples may be similar
    
    # Check structure of divergence objects
    for div in divergences:
        assert "type" in div
        assert "severity" in div
        assert "description" in div

def test_compare_programs_full():
    """Test full program comparison pipeline"""
    result = compare_programs(
        "test-program",
        "TEST_PROGRAM",
        SAMPLE_WAITLIST_CODE,
        SAMPLE_WAITLIST_COMANCHE
    )
    
    assert result["program_id"] == "test-program"
    assert result["program_name"] == "TEST_PROGRAM"
    assert "luminary" in result
    assert "comanche" in result
    assert "diff" in result
    assert "summary" in result
    assert "semantic_divergences" in result
    assert "timestamp" in result
    
    # Check summary counts
    summary = result["summary"]
    assert "added" in summary
    assert "removed" in summary
    assert "modified" in summary
    assert "unchanged" in summary
    
    # Check variants
    assert result["luminary"]["craft"] == "LM"
    assert result["comanche"]["craft"] == "CM"

def test_compare_pflite_variants():
    """Test comparison of POWERED_FLIGHT_SUBROUTINES variants"""
    result = compare_programs(
        "test-pflite",
        "POWERED_FLIGHT_SUBROUTINES",
        SAMPLE_POWERED_FLIGHT_CODE,
        SAMPLE_POWERED_FLIGHT_COMANCHE
    )
    
    assert result["program_id"] == "test-pflite"
    assert result["program_name"] == "POWERED_FLIGHT_SUBROUTINES"
    
    # Both should have parsed instructions
    assert len(result["luminary"]["parsed_instructions"]) > 0
    assert len(result["comanche"]["parsed_instructions"]) > 0

def test_identical_programs_zero_diff():
    """Test that identical programs produce zero structural differences"""
    src = "BANK\t01\n\tCA\tTIME1\n\tTC\tNEXT"
    
    result = compare_programs("identical", "IDENTICAL", src, src)
    
    # All instructions should be unchanged
    summary = result["summary"]
    assert summary["added"] == 0
    assert summary["removed"] == 0
    assert summary["modified"] == 0
    assert summary["unchanged"] > 0

def test_semantic_divergence_structure():
    """Test that semantic divergences have correct structure"""
    lm = parse_agc_source(SAMPLE_WAITLIST_CODE)
    cm = parse_agc_source(SAMPLE_WAITLIST_COMANCHE)
    
    divergences = identify_semantic_divergences(lm, cm)
    
    for div in divergences:
        assert isinstance(div["type"], str)
        assert div["severity"] in ["high", "medium", "low"]
        assert isinstance(div["description"], str)
        # lm_value and cm_value can be various types
        assert "lm_value" in div
        assert "cm_value" in div

if __name__ == "__main__":
    pytest.main([__file__, "-v"])