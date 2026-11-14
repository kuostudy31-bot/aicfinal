---
name: probe-parent
description: Temporary probe for nested dispatch. Spawns probe-child once and reports.
tools: Agent, Bash
maxTurns: 6
---
Report whether you have the Agent tool. If you do, spawn one `probe-child` subagent and reply PARENT_OK plus its reply. Also run `echo $CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` and include the output.
