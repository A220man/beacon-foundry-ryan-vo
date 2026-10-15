# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

# Change Log

All notable changes to Beacon Foundry will be documented in this file.

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
