# Universal Skill Standard (Style Guide)

**Adhere to this standard for all new skills.**

## 1. File Structure
`.agent/skills/<skill-name>/SKILL.md`

## 2. Frontmatter (YAML)
```yaml
---
name: [skill-name] (gerund form, e.g., managing-git)
description: [When to use this skill, 3rd person trigger]
version: 1.0.0
author: [gemini|claude|shared]
---
```

## 3. Body Structure
```markdown
# [Title]

## Context
When to use this skill. Why it exists.

## Prerequisites
What needs to be true (e.g., config files, installed tools).

## Workflow
High-level steps (1-5).

## Instructions
Detailed execution logic, code snippets, and rules.
```

## 4. Links
Use **Universal Relative Links** for compatibility across Obsidian, VS Code, and Agents.
- **Do:** `[Link Text](../path/to/file.md)`
- **Don't:** `[[WikiLinks]]` (unless specifically requested by user)
