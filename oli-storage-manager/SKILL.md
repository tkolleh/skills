---
name: oli-storage-manager
description: A unified data management skill using 'oli' to interface with S3, GCS, Azure, and other remote storage with built-in safety guardrails.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  tools: [oli, jq, serena, openmemory]
---

# Oli Storage Manager Skill

## When to use me
- When the user needs to interact with **remote** storage services (AWS S3, Google Cloud Storage, Azure Blob, etc.).
- When a user asks to list, move, copy, or delete files across different storage backends using `oli`.
- When the user wants to visualize the directory structure of a **remote** bucket, sftp server, or some other **remote** data store.

## What I do
- **Profile Management**: Automatically detects and prompts for `oli` profiles from `~/Library/Application Support/oli/config.toml`.
- **Data Exploration**: Generates recursive JSON tree layouts of storage directories.
- **Unified File Ops**: Executes standard file operations (`ls`, `cp`, `mv`, `rm`, `cat`, `stat`) across all OpenDAL-supported services.
- **Safety Enforcement**: Intercepts destructive actions to require explicit human confirmation.

## DO NOT USE ME FOR THE LOCAL FILE SYSTEM
- I am for **remote** only. 
- Use `serena`, `ripgrep` or `fd` when the user wants to explore the local file system.

---

## CRITICAL SAFETY RULES (MANDATORY)
**Before executing any command that modifies or deletes data, you MUST follow this protocol:**

1. **Identify Destructive Intent**: This includes `oli rm`, `oli rb`, or `oli cp`/`oli mv` when the destination already exists (overwriting).
2. **Request Explicit Confirmation**: Pause and ask: *"I am about to [Action] [Target]. Do you want to proceed? (Yes/No)"*.
3. **No Implicit Consent**: Do not proceed based on vague affirmative statements. Confirm each major batch of deletions.
4. **Pre-Check**: Use `oli stat` or `oli ls` to verify the existence of files before attempting to overwrite or delete them.

---

## 1. Profile Discovery & Validation
- **Path**: `~/Library/Application Support/oli/config.toml`
- **Action**: Parse `[profiles.name]` entries.
- **Protocol**: If no profile is provided in the prompt, list discovered profiles and ask: *"Which storage profile should I use?"*

## 2. Path & Tree Exploration
If the user requests to "explore," "layout," or "show tree":
1. Run `oli ls -R profile:/path`.
2. **Output Format**: Transform the flat list into a hierarchical **JSON** structure.
   
   **Example JSON Output:**
   ```json
   {
     "profile": "prod-s3",
     "root": "/data",
     "structure": {
       "logs": {
         "2024-01-01.log": {"type": "file", "size": "1.2MB"},
         "2024-01-02.log": {"type": "file", "size": "800KB"}
       },
       "config.json": {"type": "file", "size": "4KB"}
     }
   }
