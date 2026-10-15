import re
from typing import List, Tuple, Dict, Any, Optional
from ..models.schemas import AGCInstruction, ProofDiscrepancy, ProofResult, DiffChange, ProgramComparisonResult, ProgramVariant
from datetime import datetime, timezone
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
# Sample Comanche 055 variants for comparison
SAMPLE_WAITLIST_COMANCHE = """# Apollo 11 Comanche 055 WAITLIST.agc
# Task queue and executive timer maintenance - Command Module variant

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

SAMPLE_POWERED_FLIGHT_COMANCHE = """# Apollo 11 Comanche 055 POWERED_FLIGHT_SUBROUTINES.agc
# Throttle command and pitch attitude calculations - CM variant

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

# Note: In reality, Luminary and Comanche have significant differences in:
# - Bank assignments (LM vs CM memory map)
# - Register addresses (different hardware interfaces)
# - Additional subroutines in Luminary for lunar landing
# - Different phase tables and orbital integration routines

def compare_instructions(lm_instructions: List[AGCInstruction], cm_instructions: List[AGCInstruction]) -> List[DiffChange]:
    """Compare two parsed AGC instruction lists and produce structured diff"""
    from ..models.schemas import DiffChange
    
    diff: List[DiffChange] = []
    
    # Build lookup by label for semantic matching
    lm_by_label = {instr.label: instr for instr in lm_instructions if instr.label}
    cm_by_label = {instr.label: instr for instr in cm_instructions if instr.label}
    
    all_labels = set(lm_by_label.keys()) | set(cm_by_label.keys())
    
    # Also track by line number for structural comparison
    lm_by_line = {instr.line_number: instr for instr in lm_instructions}
    cm_by_line = {instr.line_number: instr for instr in cm_instructions}
    
    max_lines = max(len(lm_instructions), len(cm_instructions))
    
    # For each position, compare
    used_lm = set()
    used_cm = set()
    
    # First pass: match by label
    for label in sorted(all_labels):
        lm_instr = lm_by_label.get(label)
        cm_instr = cm_by_label.get(label)
        
        if lm_instr and cm_instr:
            # Both have this label - compare instructions
            changes = _compare_instruction_pair(lm_instr, cm_instr)
            diff.extend(changes)
            used_lm.add(lm_instr.line_number)
            used_cm.add(cm_instr.line_number)
        elif lm_instr and not cm_instr:
            # Label only in LM
            diff.append(DiffChange(
                type="removed",
                line_number_lm=lm_instr.line_number,
                line_number_cm=None,
                lm_instruction=lm_instr,
                cm_instruction=None,
                change_category="structure",
                description=f"Label '{label}' exists only in Luminary (LM)"
            ))
            used_lm.add(lm_instr.line_number)
        elif cm_instr and not lm_instr:
            # Label only in CM
            diff.append(DiffChange(
                type="added",
                line_number_lm=None,
                line_number_cm=cm_instr.line_number,
                lm_instruction=None,
                cm_instruction=cm_instr,
                change_category="structure",
                description=f"Label '{label}' exists only in Comanche (CM)"
            ))
            used_cm.add(cm_instr.line_number)
    
    # Second pass: remaining unmatched instructions by sequential position
    lm_remaining = [i for i in lm_instructions if i.line_number not in used_lm]
    cm_remaining = [i for i in cm_instructions if i.line_number not in used_cm]
    
    for i in range(max(len(lm_remaining), len(cm_remaining))):
        lm_instr = lm_remaining[i] if i < len(lm_remaining) else None
        cm_instr = cm_remaining[i] if i < len(cm_remaining) else None
        
        if lm_instr and cm_instr:
            changes = _compare_instruction_pair(lm_instr, cm_instr)
            diff.extend(changes)
        elif lm_instr and not cm_instr:
            diff.append(DiffChange(
                type="removed",
                line_number_lm=lm_instr.line_number,
                line_number_cm=None,
                lm_instruction=lm_instr,
                cm_instruction=None,
                change_category="structure",
                description=f"Instruction at LM line {lm_instr.line_number} has no CM counterpart"
            ))
        elif cm_instr and not lm_instr:
            diff.append(DiffChange(
                type="added",
                line_number_lm=None,
                line_number_cm=cm_instr.line_number,
                lm_instruction=None,
                cm_instruction=cm_instr,
                change_category="structure",
                description=f"Instruction at CM line {cm_instr.line_number} has no LM counterpart"
            ))
    
    return diff

def _compare_instruction_pair(lm: AGCInstruction, cm: AGCInstruction) -> List[DiffChange]:
    """Compare two individual instructions and return list of changes"""
    from ..models.schemas import DiffChange
    changes = []
    
    if lm.opcode == cm.opcode and lm.operand == cm.operand and lm.comment == cm.comment:
        changes.append(DiffChange(
            type="unchanged",
            line_number_lm=lm.line_number,
            line_number_cm=cm.line_number,
            lm_instruction=lm,
            cm_instruction=cm,
            change_category=None,
            description=f"Identical: {lm.opcode} {lm.operand or ''}"
        ))
        return changes
    
    # Check specific change categories
    if lm.opcode != cm.opcode:
        changes.append(DiffChange(
            type="modified",
            line_number_lm=lm.line_number,
            line_number_cm=cm.line_number,
            lm_instruction=lm,
            cm_instruction=cm,
            change_category="opcode",
            description=f"Opcode changed: {lm.opcode} → {cm.opcode}"
        ))
    
    if lm.operand != cm.operand:
        cat = "operand"
        if lm.operand and cm.operand:
            # Check for bank/register mapping differences
            if lm.opcode == "BANK" or cm.opcode == "BANK":
                cat = "bank"
            elif "BANK" in str(lm.operand).upper() or "BANK" in str(cm.operand).upper():
                cat = "bank"
            elif re.search(r'^[A-Z]{2,}\d*$', lm.operand or "") and re.search(r'^[A-Z]{2,}\d*$', cm.operand or ""):
                cat = "register"
        changes.append(DiffChange(
            type="modified",
            line_number_lm=lm.line_number,
            line_number_cm=cm.line_number,
            lm_instruction=lm,
            cm_instruction=cm,
            change_category=cat,
            description=f"Operand changed: {lm.operand} → {cm.operand}"
        ))
    
    if lm.label != cm.label:
        changes.append(DiffChange(
            type="modified",
            line_number_lm=lm.line_number,
            line_number_cm=cm.line_number,
            lm_instruction=lm,
            cm_instruction=cm,
            change_category="label",
            description=f"Label changed: {lm.label} → {cm.label}"
        ))
    
    if lm.comment != cm.comment:
        changes.append(DiffChange(
            type="modified",
            line_number_lm=lm.line_number,
            line_number_cm=cm.line_number,
            lm_instruction=lm,
            cm_instruction=cm,
            change_category="comment",
            description=f"Comment changed"
        ))
    
    if not changes:
        changes.append(DiffChange(
            type="modified",
            line_number_lm=lm.line_number,
            line_number_cm=cm.line_number,
            lm_instruction=lm,
            cm_instruction=cm,
            change_category="structure",
            description="Instruction differs"
        ))
    
    return changes

def identify_semantic_divergences(lm_instructions: List[AGCInstruction], cm_instructions: List[AGCInstruction]) -> List[Dict[str, Any]]:
    """Identify high-level semantic divergences between LM and CM variants"""
    divergences = []
    
    # 1. Bank assignments
    lm_banks = set()
    cm_banks = set()
    for instr in lm_instructions:
        if instr.opcode == "BANK" and instr.operand:
            lm_banks.add(instr.operand.strip())
    for instr in cm_instructions:
        if instr.opcode == "BANK" and instr.operand:
            cm_banks.add(instr.operand.strip())
    
    if lm_banks != cm_banks:
        divergences.append({
            "type": "bank_assignment",
            "severity": "high",
            "description": f"Bank assignments differ: LM uses {sorted(lm_banks)}, CM uses {sorted(cm_banks)}",
            "lm_value": sorted(list(lm_banks)),
            "cm_value": sorted(list(cm_banks))
        })
    
    # 2. SETLOC targets
    lm_setlocs = [instr.operand for instr in lm_instructions if instr.opcode == "SETLOC" and instr.operand]
    cm_setlocs = [instr.operand for instr in cm_instructions if instr.opcode == "SETLOC" and instr.operand]
    if lm_setlocs != cm_setlocs:
        divergences.append({
            "type": "memory_layout",
            "severity": "high",
            "description": f"SETLOC targets differ: LM={lm_setlocs}, CM={cm_setlocs}",
            "lm_value": lm_setlocs,
            "cm_value": cm_setlocs
        })
    
    # 3. Unique opcodes in each variant
    lm_opcodes = set(instr.opcode for instr in lm_instructions if instr.opcode not in {"LABEL_ONLY"})
    cm_opcodes = set(instr.opcode for instr in cm_instructions if instr.opcode not in {"LABEL_ONLY"})
    
    lm_only = lm_opcodes - cm_opcodes
    cm_only = cm_opcodes - lm_opcodes
    
    if lm_only:
        divergences.append({
            "type": "unique_opcodes_lm",
            "severity": "medium",
            "description": f"Opcodes only in Luminary: {sorted(lm_only)}",
            "lm_value": sorted(list(lm_only)),
            "cm_value": []
        })
    if cm_only:
        divergences.append({
            "type": "unique_opcodes_cm",
            "severity": "medium",
            "description": f"Opcodes only in Comanche: {sorted(cm_only)}",
            "lm_value": [],
            "cm_value": sorted(list(cm_only))
        })
    
    # 4. Register/operand patterns
    lm_registers = set()
    cm_registers = set()
    register_pattern = re.compile(r'^[A-Z]{2,}\d*$')
    for instr in lm_instructions:
        if instr.operand and register_pattern.match(instr.operand.strip()):
            lm_registers.add(instr.operand.strip())
    for instr in cm_instructions:
        if instr.operand and register_pattern.match(instr.operand.strip()):
            cm_registers.add(instr.operand.strip())
    
    if lm_registers != cm_registers:
        divergences.append({
            "type": "register_mapping",
            "severity": "medium",
            "description": f"Register usage differs between LM and CM variants",
            "lm_value": sorted(list(lm_registers - cm_registers)),
            "cm_value": sorted(list(cm_registers - lm_registers))
        })
    
    # 5. Instruction count difference
    if len(lm_instructions) != len(cm_instructions):
        divergences.append({
            "type": "size_difference",
            "severity": "low",
            "description": f"Instruction count differs: LM={len(lm_instructions)}, CM={len(cm_instructions)}",
            "lm_value": len(lm_instructions),
            "cm_value": len(cm_instructions)
        })
    
    return divergences

def compare_programs(program_id: str, program_name: str, lm_source: str, cm_source: str) -> Dict[str, Any]:
    """Main comparison entry point - returns full comparison result"""
    from ..models.schemas import ProgramComparisonResult, ProgramVariant
    from datetime import datetime, timezone
    
    # Parse both sources
    lm_parsed = parse_agc_source(lm_source)
    cm_parsed = parse_agc_source(cm_source)
    
    # Generate diff
    diff = compare_instructions(lm_parsed, cm_parsed)
    
    # Compute summary
    summary = {
        "added": sum(1 for d in diff if d.type == "added"),
        "removed": sum(1 for d in diff if d.type == "removed"),
        "modified": sum(1 for d in diff if d.type == "modified"),
        "unchanged": sum(1 for d in diff if d.type == "unchanged"),
    }
    
    # Identify semantic divergences
    semantic_divergences = identify_semantic_divergences(lm_parsed, cm_parsed)
    
    # Build variant objects
    lm_variant = ProgramVariant(
        craft="LM",
        program_name=program_name,
        source_code=lm_source,
        parsed_instructions=lm_parsed,
        metadata={
            "instruction_count": len(lm_parsed),
            "unique_labels": len(set(i.label for i in lm_parsed if i.label)),
            "banks_used": list(set(i.operand for i in lm_parsed if i.opcode == "BANK" and i.operand))
        }
    )
    
    cm_variant = ProgramVariant(
        craft="CM",
        program_name=program_name,
        source_code=cm_source,
        parsed_instructions=cm_parsed,
        metadata={
            "instruction_count": len(cm_parsed),
            "unique_labels": len(set(i.label for i in cm_parsed if i.label)),
            "banks_used": list(set(i.operand for i in cm_parsed if i.opcode == "BANK" and i.operand))
        }
    )
    
    result = ProgramComparisonResult(
        program_id=program_id,
        program_name=program_name,
        luminary=lm_variant,
        comanche=cm_variant,
        diff=diff,
        summary=summary,
        semantic_divergences=semantic_divergences,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return result.model_dump()
