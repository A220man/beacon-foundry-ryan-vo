# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

# Change Log

All notable changes to Beacon Foundry will be documented in this file.

## [1.0.0] - 2026-10-12
### Added
- Initial release of Beacon Foundry: AI/ML developer tools for Apollo Guidance Computer proofing, telemetry trajectory evaluation, and ML alignment verification.
- Modular FastAPI backend with persistent SQLite storage, OIDC/Keycloak authentication + local demo mode, audit logging, and multi-provider LLM advisory integration.
- Deterministic AGC AST parser and token-level proofing against historical transcription scans.
- Guidance law state vector simulator with trajectory deviation detection and anomaly classification.
- Reproducible ML evaluation pipeline comparing heuristic baseline vs embedding cosine alignment with labeled ground-truth transcription anomalies.
- Full React + TypeScript + Vite frontend with operational dashboards, trajectory visualization, proofing diff viewer, and evaluation benchmarks.
- Docker containerization and CI automation with pytest and vitest workflows.
