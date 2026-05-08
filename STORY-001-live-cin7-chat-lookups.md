# STORY-001 Live Cin7 Chat Lookups

## Parent Feature

- `FEATURE-001-cin7-read-only-mcp.md`

## User Story

As an operator, I want to ask chat questions like "what is the average cost of SKU X", "how many units of Y did we sell last month", or "how many units of X did we order" so that I can get current Cin7 answers without manually using the Cin7 UI.

## Acceptance Criteria

- A new skill exists for live Cin7 Core lookups.
- The skill documents when to use focused tools versus the generic GET fallback.
- A Python MCP server can run with Cin7 credentials from environment variables.
- The server exposes product lookup, product cost, inventory availability, sale list/detail, purchase list/detail, units sold, units ordered, and raw GET tools.
- Documentation includes command-line usage, environment variables, expected outputs, and MCP client configuration examples.
- `status.md` reflects the current state of the work.

## Risks

- "Units sold" is definition-sensitive: ordered, invoiced, fulfilled, and net-of-credit-note results can differ.
- ChatGPT support is more deployment-heavy than local Claude/Codex usage because local `stdio` is not the same as a hosted connector.

## Downstream Impacts

- Additional stories should extend the focused tool set for reorder levels, customer sales history, and supplier cost history.
