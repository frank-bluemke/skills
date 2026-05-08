# Setup Guide

The bundled MCP server is read-only and expects Cin7 credentials in environment variables:

- `CIN7_ACCOUNT_ID`
- `CIN7_APPLICATION_KEY`
- optional: `CIN7_BASE_URL`
- optional: `CIN7_RATE_LIMIT_PER_MINUTE`

## Local MCP Clients

Use local `stdio` transport for Codex, Claude Code, or clients that support local MCP server commands directly.

Recommended command:

```bash
uv run --with mcp python /absolute/path/to/cin7_core_live_mcp.py
```

## Remote MCP Clients

For clients that expect a hosted MCP endpoint, run the same server over HTTP:

```bash
uv run --with mcp python /absolute/path/to/cin7_core_live_mcp.py --transport streamable-http --host 0.0.0.0 --port 8000
```

Then expose that port through your preferred HTTPS tunnel or deployment target.

The script also accepts `--transport http` as a compatibility alias for SDK versions that still use that transport name.

## Operating Notes

- The server only performs `GET` requests against Cin7 Core.
- Product cost answers come from the Product `AverageCost` field by default.
- Inventory availability answers come from `/ref/productavailability`.
- Quantity aggregation can be slower than simple lookups because Cin7 line data lives on sale detail endpoints.
- Ordered-units answers currently aggregate `Purchase.Order.Lines` from `/purchase`, which the blueprint documents as the simple-purchase detail endpoint.
