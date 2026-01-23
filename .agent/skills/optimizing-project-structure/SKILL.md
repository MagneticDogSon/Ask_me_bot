---
name: optimizing-project-structure
description: Analyzes project organization, removes unused assets, and enforces architectural standards. Use when the user wants to clean, structure, or organize the codebase.
---

# Project Optimization & Cleanup

## When to use this skill
- User asks to "clean up" the project.
- User wants to "structure" or "organize" files.
- User mentions deleting "junk", "unused files", or "old code".
- The project root is cluttered with loose files.

## Workflow

### 1. Discovery & Analysis
- [ ] Run `python .agent/skills/optimizing-project-structure/scripts/analyze_project.py` to get a statistical overview of file types and root-level clutter.
- [ ] List directories to identify non-standard folders (e.g., `backup`, `old`, `stuff`).
- [ ] Identify "Rot":
    -   Extensions: `.log`, `.tmp`, `.bak`, `.old`, `.orig`
    -   Names: `copy`, `features_backup`, `test_old`
    -   Empty directories.

### 2. Proposal (Crucial Step)
- [ ] Draft a **Restructuring Plan** in markdown.
    -   **Delete**: List specific files/folders to remove.
    -   **Move**: `file_a.py` -> `src/utils/file_a.py`.
    -   **Create**: New folders (e.g., `src/`, `docs/`, `config/`).
- [ ] **STOP** and ask the user to confirm the plan. *Never delete code without explicit approval.*

### 3. Execution
- [ ] **Delete**: Use `Remove-Item` for approved deletions.
- [ ] **Structure**: Use `Move-Item` to organize files.
- [ ] **Standardize**: Ensure entry points (main.py, app.py) are in logical places.

### 4. Verification
- [ ] Run the project (if applicable) to ensure no dependencies were broken.
- [ ] Check `import` statements if files were moved (grep for moved filenames).

## Best Practices
- **Root Directory Hygiene**: The root should only contain configuration (`.gitignore`, `README.md`, `requirements.txt`) and key entry points. Everything else goes into `src/`, `docs/`, or `scripts/`.
- **Grouping**: Group by feature (e.g., `auth/`, `payments/`) or by type (`middleware/`, `models/`), but pick **one** strategy and stick to it.
- **Safety**: When in doubt, move to `_archive/` instead of deleting.
