# System Architecture: The "Second Brain" Protocol

**To:** Future Agents (Gemini, Claude, New Agents)
**From:** Showrunner Configuration
**Date:** 2026-02-05

## 1. Executive Summary (The "So What")
We have transitioned from **isolated, per-project agent knowledge** to a **centralized Second Brain** model. This allows all agents, regardless of their workspace or model, to share a single, evolving library of "Skills" (tools/instructions). We also implemented a **Coordination Server** to ensure we don't conflict when working on the same files.

## 2. The Architecture
### Physical Layout
*   **Central Truth (The Brain):** `C:\Users\Angel\Documents\App Dev Vault\skills`
    *   This is the master folder managed by the User via Obsidian.
*   **Agent Access (The Junctions):**
    *   **Showrunner (Gemini):** `.agent/skills` is a **Directory Junction** pointing to the Central Truth.
    *   **Claude Code:** `.claude/skills` is a **Directory Junction** pointing to the Central Truth.

### capabilities
*   **Instant Skill Sharing:** If Gemini invents a `research-paper-parser` skill, Claude can use it instantly. No git push/pull required.
*   **Unified Memory:** We share the same instructional set for standard tasks (`auto-pr`, `tdd-design`).
*   **Traffic Control:** We use `~/.antigravity/coordination/server.py` to:
    *   **Check In/Out**: Signal availability.
    *   **Lock Files**: Prevent race conditions (`lock <agent> <file>`).
    *   **Handoff**: Pass tailored tasks to each other (`handoff <from> <to> <task_id> <context>`).

## 3. Operational Protocols
### Using Skills
*   **Read-Only Default:** Treat the `skills` folder as read-only unless instructed to create a verified skill.
*   **Discovery:** Always list the `skills` directory to see what capabilities are available (`dev-`, `fin-`, `gen-` prefixes).

### Coordination
*   **Lock Before Write:** Before editing shared code, run `python server.py lock ...`.
*   **PowerShell Quoting:** When sending JSON metadata in handoffs via PowerShell, use the **Stop Parsing** operator:
    *   `python server.py --% handoff gemini claude task-xyz "{\"note\":\"safe\"}" low`

## 4. Restraints & Risks
*   **Junction Safety:** **NEVER** run `rm -rf` on the `skills` folder. Since it is a junction, you might unknowingly delete the master copy in the User's Vault. Unlink carefully if needed.
*   **Platform Specifics:** This architecture relies on Windows `mklink /J` or `New-Item -Type Junction`. Standard symlinks may require admin privileges and fail.
