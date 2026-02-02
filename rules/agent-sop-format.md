---
description: Standard format for Agent SOPs (aligned with agent-sop)
globs: **/*.sop.md
---
# Agent SOP Format

SOPs in this project use the same structure as [agent-sop](https://github.com/strands-agents/agent-sop).

## Required

- File extension: `.sop.md`
- Sections: **Overview**, **Parameters**, **Steps**
- Steps use **Constraints** with RFC 2119 keywords (MUST, SHOULD, MAY)

## Parameter style

- **param_name** (required): description  
- **optional_param** (optional, default: value): description  

## Steps

- Each step: `### N. Step Name` + description + **Constraints:** bullet list.

## Optional sections

- **Examples**, **Troubleshooting**
