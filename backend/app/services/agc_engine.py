import re
from typing import List, Tuple, Dict, Any, Optional
from ..models.schemas import AGCInstruction, ProofDiscrepancy, ProofResult

VALID_OPCODES = {
    # Basic instructions
    "TC", "CCS", "TCF", "DAS", "LXCH", "INCR", "ADS", "CA", "CS", "INDEX", 
    "DXCH", "TS", "XCH", "AD", "MASK", "READ", "WRITE", "RAND", "WAND", "ROR", 
    "WOR", "RXOR", "EDOP", "EXTEND",
    # Ext-opcodes
    "MP", "DV", "BZF", "MSU", "QXCH", "AUG", "DIM", "DTCB", "DTCF", "OVSK",
    # Pseudo-ops & Banks
    "SETLOC", "BANK", "COUNT", "COUNT*", "BLOCK", "EBANK", "SBANK", "2CADR", "CADR", 
    "EQUALS", "DEC", "OCT", "ERASE", "BBCON", "NOOP", "RETURN", "CAF", "VLOAD",
    "STODL", "BOV", "RTB", "STORE", "SUBCALL", "UNIT"
}

SAMPLE_WAITLIST_CODE = """# Apollo 11 Luminary 099 WAITLIST.agc
# Task queue and executive timer maintenance

		BANK	01
		SETLOC	WAITLOC
		COUNT*	$$/WAIT

WAITLIST	CA	TIME1
		TC	CHECKTIM
		CCS	WAITEXIT
		TCF	+2
		TC	TASKOVER

CHECKTIM	INDEX	Q
		CA	0
		AD	ITEMP1
		TS	L
		TC	WAITLOOP

TASKOVER	EXTEND
		DTCB
"""

SAMPLE_POWERED_FLIGHT_CODE = """# Apollo 11 Luminary 099 POWERED_FLIGHT_SUBROUTINES.agc
# Throttle command and pitch attitude calculations

		BANK	32
		SETLOC	POWFLITE
		COUNT*	$$/PFLITE

PFLTSTRT	CA	PIPAX
		TS	DELV
		CS	PIPAY
		ADS	DELV +1
		EXTEND
		MP	KTHROTTLE
		TS	FCOMMAND
		TC	RETURN
"""

def parse_agc_source(source_text: str) -> List[AGCInstruction]:
    instructions: List[AGCInstruction] = []
    lines = source_text.splitlines()
    
    for idx, raw_line in enumerate(lines, start=1):
        clean = raw_line.strip()
        if not clean or clean.startswith("#"):
            continue
        
        # Strip comments
        comment = None
        if "#" in raw_line:
            parts = raw_line.split("#", 1)
            raw_code = parts[0]
            comment = parts[1].strip()
        else:
            raw_code = raw_line
            
        tokens = raw_code.strip().split()
        if not tokens:
            continue
            
        label = None
        opcode = ""
        operand = None
        
        # Check if first token is an opcode (indented or no label)
        if raw_line.startswith((" ", "\t")):
            opcode = tokens[0].upper()
            if len(tokens) > 1:
                operand = " ".join(tokens[1:])
        elif tokens[0].upper() in VALID_OPCODES:
            opcode = tokens[0].upper()
            if len(tokens) > 1:
                operand = " ".join(tokens[1:])
        else:
            # First token is label
            label = tokens[0]
            if len(tokens) > 1:
                opcode = tokens[1].upper()
                if len(tokens) > 2:
                    operand = " ".join(tokens[2:])
            else:
                opcode = "LABEL_ONLY"

        instructions.append(AGCInstruction(
            line_number=idx,
            label=label,
            opcode=opcode,
            operand=operand,
            comment=comment,
            raw=raw_line
        ))
        
    return instructions

def proof_transcription(transcription_text: str, baseline_reference: str = "Luminary099-Scan") -> ProofResult:
    parsed = parse_agc_source(transcription_text)
    discrepancies: List[ProofDiscrepancy] = []
    
    for item in parsed:
        if item.opcode == "LABEL_ONLY":
            continue
        # Check 1: Unknown AGC opcode
        if item.opcode not in VALID_OPCODES:
            discrepancies.append(ProofDiscrepancy(
                line_number=item.line_number,
                issue_type="OPCODE_MISMATCH",
                scanned_text=f"[Standard Opcode expected on line {item.line_number}]",
                transcribed_text=item.raw.strip(),
                confidence=0.95,
                suggestion=f"Opcode '{item.opcode}' unrecognized in AGC instruction set. Did scan transcribe 'TC', 'CCS', or 'EXTEND'?"
            ))
            
        # Check 2: Missing expected operand
        if item.opcode in {"CA", "CS", "TS", "TC", "INDEX", "AD", "ADS", "MP", "DV"} and not item.operand:
            discrepancies.append(ProofDiscrepancy(
                line_number=item.line_number,
                issue_type="MISSING_OPERAND",
                scanned_text=f"{item.opcode} <REGISTER_OR_TAG>",
                transcribed_text=item.raw.strip(),
                confidence=0.88,
                suggestion=f"Memory reference instruction '{item.opcode}' requires a register or memory location."
            ))
            
        # Check 3: Check for OCR misreading common characters (e.g. '0' vs 'O', '1' vs 'I')
        if item.operand and re.search(r'\b[0-9]+[OIl]\b', item.operand):
            discrepancies.append(ProofDiscrepancy(
                line_number=item.line_number,
                issue_type="SYNTAX_ANOMALY",
                scanned_text="Octal or Register constant",
                transcribed_text=item.operand,
                confidence=0.92,
                suggestion="Potential OCR transcription mixup between digits and letters (e.g., 0 vs O, 1 vs I)."
            ))

    total = len(parsed)
    issues_count = len(discrepancies)
    quality_score = max(0.0, 1.0 - (issues_count / max(1, total))) if total > 0 else 0.0
    
    return ProofResult(
        total_lines=len(transcription_text.splitlines()),
        parsed_instructions=total,
        discrepancies=discrepancies,
        quality_score=round(quality_score, 3),
        status="PASSED" if issues_count == 0 else "DISCREPANCIES_DETECTED"
    )
