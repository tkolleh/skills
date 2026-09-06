# Agent skills

A collection of AI agent "skills" following the [OpenCode agent skills](https://opencode.ai/docs/skills/#write-frontmatter) format (open agent skills). 

> Skills are reusable capabilities for AI agents. They provide procedural knowledge that helps agents accomplish specific tasks more effectively. Skills can include code generation patterns, domain expertise, tool integrations, and more.

## Usage

**Setup a skill**

```zsh
skillshare install tkolleh/skills/<skill>
skillshare sync
```

Skills are installed from this repo into the shared skillshare source
(`~/.config/skillshare/skills/`), then synced to the configured targets
(Claude Code, OpenCode, universal).
