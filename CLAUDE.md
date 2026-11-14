# Project instructions

The instructor's finance practitioner profile applies to this project:

@AGENTS.md

## Notes for Claude Code

`AGENTS.md` above is copied unchanged from the course's Kimi Code bundle. Where it
assumes Kimi-specific tooling, read it as follows:

- **Skills:** the practitioner skills live in `.claude/skills/` (brainstorming,
  frontend-design, git, humanize, latex, newproj, plot).
- **External data:** the `kimi-datasource` plugin is not available in Claude Code.
  Fetch external financial data only from the sources the task permits (for
  example SEC EDGAR or FRED), and record the source, retrieval time and as-of date
  next to the data.
- **Git:** when the session or user specifies a working branch, push only to that
  branch, even if the `git` skill's default would push elsewhere.
