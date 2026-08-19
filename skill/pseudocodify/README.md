# pseudocodify (skill)

Coding-agent skill that wraps the [`pseudocodify`](https://github.com/keithmackay/pseudocodify) CLI to convert a codebase into human-readable, language-agnostic pseudocode.

## Installation

### Claude Code

```bash
cp -r /path/to/pseudocodify/ ~/.claude/skills/pseudocodify/
```

Or symlink:
```bash
ln -s /path/to/pseudocodify/ ~/.claude/skills/pseudocodify
```

Then invoke with: `/pseudocodify`

### Codex

Place the plugin directory where Codex can find it, then add an entry to your marketplace:

**`~/.agents/plugins/marketplace.json`** (create if absent):
```json
{
  "name": "personal",
  "interface": { "displayName": "Personal Plugins" },
  "plugins": [
    {
      "name": "pseudocodify",
      "source": { "source": "local", "path": "/path/to/pseudocodify/" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```

### Antigravity

**Global install** (all workspaces):
```bash
cp -r /path/to/pseudocodify/ ~/.gemini/antigravity/skills/pseudocodify/
```

**Workspace install** (current project only):
```bash
cp -r /path/to/pseudocodify/ .agents/skills/pseudocodify/
```

The root `SKILL.md` has no Claude Code-specific metadata, so it is used as-is — no separate Antigravity variant is needed.

Skills are auto-discovered. You can also mention the skill by name to force activation.

### Gemini CLI

Gemini CLI installs extensions directly from GitHub:

```bash
gemini extensions install https://github.com/<owner>/pseudocodify-skill
```

To update:
```bash
gemini extensions update pseudocodify
```

The skill is auto-discovered from `GEMINI.md` after installation. Local install is not directly supported — the skill directory must live in a GitHub repository.

## Compatibility

| Feature | Claude Code | Codex | Antigravity | Gemini CLI |
|---------|:-----------:|:-----:|:-----------:|:----------:|
| Core skill | ✅ | ✅ | ✅ | ✅ |

No Claude Code-specific frontmatter (`metadata`, `retrieval`, `tags`), sub-documents, or subagent dispatch is used by this skill, so there are no platform gaps to document — it ports cleanly to all four platforms.

Legend: ✅ Supported · ❌ Not supported

## References

- **Claude Code Skills:** https://code.claude.com/docs/en/skills
- **Claude Code Complete Guide (PDF):** https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf
- **Codex Plugins:** https://developers.openai.com/codex/plugins/build
- **Antigravity Skills:** https://antigravity.google/docs/skills
- **Gemini CLI Extensions:** https://github.com/google-gemini/gemini-cli/blob/main/docs/extension.md
- **Agent Skills open standard:** https://agentskills.io/home
- **pseudocodify CLI:** https://github.com/keithmackay/pseudocodify
