# Instructions

`instructions/global.md` holds instructions for every project, in plain Markdown.

- **Claude Code:** `setup-mstack` writes it as a managed block in `~/.claude/CLAUDE.md` with `mstack merge-block instructions/global.md ~/.claude/CLAUDE.md --dry-run|--write`. Only the text between `<!-- mstack:begin -->` and `<!-- mstack:end -->` is replaced; everything outside the markers stays the user's.
- **Cursor:** printed for Cursor Settings → Rules → User Rules, like the rules.

Keep it short, in English, and free of domain details and machine-specific paths.

Nothing is shipped yet.
