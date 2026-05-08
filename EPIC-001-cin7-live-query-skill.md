# EPIC-001 Cin7 Live Query Skill

## Goal

Create a Codex skill that answers live, read-only Cin7 Core questions from chat by combining:

- the existing `cin7-core-api` blueprint skill for endpoint selection and request rules
- a bundled MCP server that uses the operator's Cin7 API credentials to make authenticated requests

## Business Value

- Lets an operator ask ad hoc questions such as product cost, pricing, and units sold without leaving chat.
- Keeps the integration read-only for safer day-to-day use.
- Provides a reusable path for Claude, Codex, and ChatGPT-style MCP clients.

## Scope

- New skill folder for live Cin7 Core lookups
- Read-only MCP server with focused tools
- Human setup documentation for local and remote MCP usage
- Planning and status tracking artifacts required by this repository

## Out Of Scope

- Write or mutation endpoints
- OAuth or multi-user auth flows
- Production deployment automation for a hosted MCP service

## Downstream Impacts

- Future live queries can be added as more MCP tools without changing the overall skill shape.
- If ChatGPT workspace connector requirements change, only the deployment/config docs should need revision; the Cin7 read-only server can stay the same.
