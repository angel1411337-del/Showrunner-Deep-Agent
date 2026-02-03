# Project Constitution

> These principles are **non-negotiable**. All agents, all sessions, all code must comply.
> Violations require explicit human approval and documentation in decisions.md.

## Last Updated
2026-02-03

## 1. Quality Standards

### 1.0 Test-First Development
**Rule:** Write tests before implementing production changes. Any `src/` change must be accompanied by `tests/` updates.
**Rationale:** Keeps design driven by tests and prevents unverified changes.
**Violation Response:** block

### 1.1 Tests Must Pass
**Rule:** `pytest` must pass for all changes that touch production logic.
**Rationale:** Prevents regressions and keeps the golden determinism suite stable.
**Violation Response:** block

### 1.2 Static Checks Must Be Clean
**Rule:** `ruff` and `pyright` must be clean for changes under `src/`.
**Rationale:** Maintains code quality and strict typing guarantees.
**Violation Response:** block

### 1.3 Deterministic Outputs
**Rule:** Any IDs, hashes, and exported artifacts must be deterministic for the same inputs.
**Rationale:** Golden tests and reproducibility are core to the pipeline.
**Violation Response:** block

## 2. Security Constraints

### 2.1 No Secrets in Repo
**Rule:** API keys, tokens, or credentials must never be committed. Use env vars.
**Rationale:** Prevents credential leakage.
**Violation Response:** block

### 2.2 External LLM Calls Are Optional
**Rule:** LLM-backed features must be optional and disabled by default in tests/CI.
**Rationale:** Ensures offline, deterministic test runs.
**Violation Response:** block

### 2.3 PII Handling
**Rule:** Do not store or export PII unless explicitly required and documented.
**Rationale:** Avoids privacy risk.
**Violation Response:** warn

## 3. Coding Principles

### 3.1 Typed, Explicit APIs
**Rule:** Public APIs must have type hints and clear docstrings.
**Rationale:** Supports strict typing and maintainability.
**Violation Response:** warn

### 3.2 No Bare Exceptions
**Rule:** Avoid `except:` and overly broad exception handling; catch explicit errors.
**Rationale:** Prevents masking real failures.
**Violation Response:** warn

### 3.3 Prefer Immutable Contracts
**Rule:** Domain contracts should be immutable (frozen Pydantic models) unless justified.
**Rationale:** Prevents accidental mutation across pipeline stages.
**Violation Response:** warn

## 4. Architectural Boundaries

### 4.1 Contracts Are Source of Truth
**Rule:** `src/showrunner/contracts` defines the canonical data models.
**Rationale:** Keeps all stages consistent and reduces drift.
**Violation Response:** block

### 4.2 Dependency Direction
**Rule:** Pipeline/orchestrator may depend on components, but components must not depend on pipeline.
**Rationale:** Maintains modularity and testability.
**Violation Response:** block

### 4.3 Providers Are Pluggable
**Rule:** LLM usage must go through provider interfaces in `src/showrunner/providers`.
**Rationale:** Enables offline and multi-provider support.
**Violation Response:** block

## 5. Testing Requirements

### 5.1 Golden Tests Are Mandatory
**Rule:** Golden determinism tests must pass and be updated only with explicit approval.
**Rationale:** Prevents silent drift in outputs.
**Violation Response:** block

### 5.2 Contract Tests For New Interfaces
**Rule:** Any new provider or interface must include a consumer-driven contract test.
**Rationale:** Prevents semantic drift between components.
**Violation Response:** warn

## Amendment Process

To amend this constitution:
1. Propose change in `.claude/docs/decisions.md`
2. Get explicit human approval
3. Document rationale for the change
4. Update this file
