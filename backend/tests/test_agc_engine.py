import pytest
from app.services.agc_engine import (
    parse_agc_source, proof_transcription,
    SAMPLE_WAITLIST_CODE, SAMPLE_POWERED_FLIGHT_CODE
)

def test_parse_valid_agc_source():
    instructions = parse_agc_source(SAMPLE_WAITLIST_CODE)
    assert len(instructions) > 5
    opcodes = [i.opcode for i in instructions]
    assert "CA" in opcodes
    assert "TC" in opcodes
    assert "INDEX" in opcodes

def test_parse_comments_and_labels():
    src = "START\tCA\tTIME1 # Load current clock\n\tTC\tNEXT\nNEXT\tEXTEND"
    instructions = parse_agc_source(src)
    assert len(instructions) == 3
    assert instructions[0].label == "START"
    assert instructions[0].opcode == "CA"
    assert instructions[0].operand == "TIME1"
    assert instructions[0].comment == "Load current clock"
    assert instructions[2].label == "NEXT"
    assert instructions[2].opcode == "EXTEND"

def test_proof_clean_code():
    res = proof_transcription(SAMPLE_POWERED_FLIGHT_CODE)
    assert res.status == "PASSED"
    assert res.quality_score == 1.0
    assert len(res.discrepancies) == 0

def test_proof_detects_unknown_opcode():
    corrupted = "MYTAG\tBADOP\tARG1"
    res = proof_transcription(corrupted)
    assert res.status == "DISCREPANCIES_DETECTED"
    assert len(res.discrepancies) == 1
    assert res.discrepancies[0].issue_type == "OPCODE_MISMATCH"

def test_proof_detects_missing_operand():
    corrupted = "\tCA\n\tTC\n"
    res = proof_transcription(corrupted)
    assert res.status == "DISCREPANCIES_DETECTED"
    assert any(d.issue_type == "MISSING_OPERAND" for d in res.discrepancies)

def test_proof_detects_ocr_confusion():
    corrupted = "\tCA\t123O\n" # 123O ending in letter O instead of 0
    res = proof_transcription(corrupted)
    assert any(d.issue_type == "SYNTAX_ANOMALY" for d in res.discrepancies)
