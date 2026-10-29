# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

scan-reference-integration

## Roadmap

### core-baseline — Core Apollo Guidance Computer Proofing & ML Alignment Platform

Status: done

Acceptance:
- Full FastAPI modular backend with OIDC/demo auth, AGC AST parsing, trajectory simulation, and ML evaluation
- React + TS frontend dashboard with interactive telemetry, AGC diff viewer, and benchmark charts
- Passing unit, integration, and security test suites

Implementation: `backend/app/main.py`, `backend/app/api/endpoints.py`, `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/models/schemas.py`, `backend/app/services/agc_engine.py`, `backend/app/services/trajectory_engine.py`, `backend/app/services/ml_eval_runner.py`, `backend/app/services/llm_adapter.py`, `backend/app/services/database.py`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`

Tests: `backend/tests/test_api.py`, `backend/tests/test_agc_engine.py`, `backend/tests/test_trajectory.py`, `backend/tests/test_ml_eval.py`, `backend/tests/test_auth.py`, `frontend/src/App.test.tsx`

### agc-program-comparison — AGC Program Comparison: Luminary099 vs Comanche055 Side-by-Side Diff

Status: done

Acceptance:
- New endpoint /api/v1/agc/compare/{program_id} returns structured diff between LM and CM versions
- Database stores both Luminary and Comanche program variants with metadata
- Frontend Comparison tab renders side-by-side opcode/operand diff with anomaly highlighting
- AST-level semantic diff identifies bank/register divergences, not just textual changes
- Unit and integration tests for comparison engine and API

Implementation: `backend/app/services/agc_engine.py`, `backend/app/services/database.py`, `backend/app/models/schemas.py`, `backend/app/api/endpoints.py`, `frontend/src/components/ComparisonViewer.tsx`, `frontend/src/api/client.ts`, `frontend/src/App.tsx`

Tests: `backend/tests/test_agc_comparison.py`, `backend/tests/test_api.py`

### scan-reference-integration — Historical Scan Reference Integration for Transcription Verification

Status: done

Acceptance:
- New endpoint /api/v1/agc/scan-reference/{program_id}/{page_range} fetches scan metadata from ibiblio.org
- Frontend Proofing tab shows scan reference panel with page numbers and URLs
- Proofing results display corresponding scan page links for each discrepancy
- Offline fallback: cached scan metadata when network unavailable
- Unit and integration tests for scan reference service and API

Implementation: `backend/app/services/scan_reference.py`, `backend/app/api/endpoints.py`, `backend/app/models/schemas.py`, `frontend/src/components/ScanReferencePanel.tsx`, `frontend/src/api/client.ts`, `frontend/src/App.tsx`

Tests: `backend/tests/test_scan_reference.py`, `backend/tests/test_api.py`

### agc-ocr-correction — AGC Transcription OCR Error Detection & Correction

Status: planned

Acceptance:
- OCR error pattern detection for common AGC transcription artifacts (O/0, I/1, S/5, B/8, Z/2, D/0)
- Endpoint /api/v1/agc/ocr-correct/{program_id} returns corrected transcription with confidence scores
- Frontend Proofing tab shows OCR correction suggestions inline with original text
- Integration with existing proofing pipeline for automated pre-processing
- Unit and integration tests for OCR correction engine and API

Implementation: `backend/app/services/ocr_correction.py`, `backend/app/api/endpoints.py`, `backend/app/models/schemas.py`, `frontend/src/components/OCRCorrectionPanel.tsx`, `frontend/src/api/client.ts`, `frontend/src/App.tsx`

Tests: `backend/tests/test_ocr_correction.py`, `backend/tests/test_api.py`

