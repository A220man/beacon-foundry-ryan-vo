# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.1.1] - 2026-10-22
### Added
- Historical Scan Reference Integration for AGC transcription verification
- New backend service `scan_reference.py` with curated catalog of 7 Apollo 11 scan references from ibiblio.org (WAITLIST, POWERED_FLIGHT_SUBROUTINES, PHASE_TABLE_MAINTENANCE, ORBITAL_INTEGRATION, TIME_OF_FREE_FALL, TJET_LAW, P20-P25)
- REST endpoints: `/api/v1/agc/scan-reference/{program_id}`, `/api/v1/agc/scan-reference/{program_id}/discrepancy/{line_number}`, `/api/v1/agc/scan-catalog`
- Pydantic models: `ScanMetadata`, `ScanPageReference`, `DiscrepancyScanReference`
- Frontend `ScanReferencePanel` component integrated into Proofing tab showing scan page ranges, quality ratings, and direct links to historical scans
- Per-discrepancy scan page estimation with direct links for verification
- Offline fallback with local JSON cache and curated scan metadata
- 11 new unit tests (`test_scan_reference.py`) and 4 API integration tests
- All 58 backend tests and 4 frontend tests pass

## [1.1.0] - 2026-10-15
### Added
- AGC Program Comparison: Side-by-side Luminary 099 (Lunar Module) vs Comanche 055 (Command Module) diff viewer
- New REST endpoint `/api/v1/agc/compare/{program_id}` returning structured AST-level semantic diff
- Database schema extension with `agc_program_variants` table for storing LM/CM variant pairs with metadata
- Frontend "LM vs CM Comparison" tab with color-coded diff: added (green), removed (red), modified (amber), unchanged (collapsed)
- Semantic divergence detection: bank assignment differences, memory layout (SETLOC), unique opcodes per variant, register mapping differences
- Comparison engine tests: 9 new unit/integration tests covering opcode, operand, bank, and structural diff detection
- Pre-seeded database with WAITLIST and POWERED_FLIGHT_SUBROUTINES variants for both Luminary and Comanche

## [1.0.0] - 2026-10-12
### Added
- Initial release of Beacon Foundry: AI/ML developer tools for Apollo Guidance Computer proofing, telemetry trajectory evaluation, and ML alignment verification.
- Modular FastAPI backend with persistent SQLite storage, OIDC/Keycloak authentication + local demo mode, audit logging, and multi-provider LLM advisory integration.
- Deterministic AGC AST parser and token-level proofing against historical transcription scans.
- Guidance law state vector simulator with trajectory deviation detection and anomaly classification.
- Reproducible ML evaluation pipeline comparing heuristic baseline vs embedding cosine alignment with labeled ground-truth transcription anomalies.
- Full React + TypeScript + Vite frontend with operational dashboards, trajectory visualization, proofing diff viewer, and evaluation benchmarks.
- Docker containerization and CI automation with pytest and vitest workflows.