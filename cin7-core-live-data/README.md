# Cin7 Core Live Data Skill

This skill adds a read-only MCP server for live Cin7 Core lookups so a chat agent can answer questions such as:

- "What is the average cost of SKU `ABC-123`?"
- "Show me the current price tiers for Baked Bread."
- "What is available for SKU `ABC-123` in Main Warehouse?"
- "How many units of Bread did we sell between 2026-03-01 and 2026-03-31?"
- "How many units of Bread did we order last month?"

It is designed to complement the existing `cin7-core-api` blueprint skill. The new skill handles live lookups, while the blueprint skill remains the source of truth for endpoint selection and request-shape details.

## Files

- `SKILL.md`: skill instructions for Codex-style agents
- `scripts/cin7_core_live_mcp.py`: read-only MCP server
- `references/setup-guide.md`: concise setup notes for local and remote MCP clients
- `references/query-patterns.md`: tool selection guidance for common questions

## Requirements

- Python 3.10+
- The Python `mcp` package available in the runtime used to launch the server
- Valid Cin7 Core API credentials

## Environment Variables

Required:

- `CIN7_ACCOUNT_ID`
- `CIN7_APPLICATION_KEY`

Optional:

- `CIN7_BASE_URL`
  - Default: `https://inventory.dearsystems.com/ExternalApi/v2`
- `CIN7_RATE_LIMIT_PER_MINUTE`
  - Default: `55`

Example:

```bash
export CIN7_ACCOUNT_ID="your-account-id"
export CIN7_APPLICATION_KEY="your-application-key"
export CIN7_RATE_LIMIT_PER_MINUTE="55"
```

## CLI Usage

Run as a local `stdio` MCP server:

```bash
uv run --with mcp python cin7-core-live-data/scripts/cin7_core_live_mcp.py
```

Run as an HTTP MCP server for a remotely reachable connector:

```bash
uv run --with mcp python cin7-core-live-data/scripts/cin7_core_live_mcp.py --transport streamable-http --host 0.0.0.0 --port 8000
```

Show CLI help:

```bash
python cin7-core-live-data/scripts/cin7_core_live_mcp.py --help
```

## Claude Or Codex Local MCP Configuration

Example `.mcp.json` entry:

```json
{
  "mcpServers": {
    "cin7-core-live": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp",
        "python",
        "/absolute/path/to/cin7-core-live-data/scripts/cin7_core_live_mcp.py"
      ],
      "env": {
        "CIN7_ACCOUNT_ID": "your-account-id",
        "CIN7_APPLICATION_KEY": "your-application-key",
        "CIN7_RATE_LIMIT_PER_MINUTE": "55"
      }
    }
  }
}
```

## ChatGPT MCP Deployment Shape

If your ChatGPT workspace supports custom MCP connectors, you will need a remotely reachable MCP endpoint rather than a local `stdio` command. The simplest path is:

1. Start the server with `--transport streamable-http`.
   - The script also accepts `--transport http` and will fall back between common SDK transport names.
2. Put it behind HTTPS with a tunnel or deployment target.
3. Register that URL as your custom MCP connector in ChatGPT.

The server code stays the same; only the transport and hosting change.

## Exposed Tools

- `find_products`
  - Search products by partial SKU or name.
- `get_product_cost`
  - Return `AverageCost`, price tiers, and optional supplier costs for a product.
- `get_product_availability`
  - Return availability rows from `/ref/productavailability`, including on-hand, allocated, available, on-order, and in-transit values.
- `list_sales`
  - Return sale list rows from `/saleList`.
- `get_sale`
  - Return the full `/sale` payload for a specific `SaleID`.
- `list_purchases`
  - Return purchase list rows from `/purchaseList`.
- `get_purchase`
  - Return the full `/purchase` payload for a specific purchase `ID`.
- `get_units_sold`
  - Aggregate quantities for matching products across sale details.
- `get_units_ordered`
  - Aggregate quantities from `Purchase.Order.Lines` across matching purchase details.
- `raw_get`
  - Read-only GET escape hatch for other blueprint-backed endpoints.

## Expected Outputs

The MCP server returns structured tool responses such as:

- matching product records
- product cost summaries
- inventory availability rows
- sale summaries or full sale details
- purchase summaries or full purchase details
- units-sold aggregates with truncation metadata
- units-ordered aggregates with truncation metadata
- raw GET payloads from Cin7 Core

Console output is minimal unless the MCP host process surfaces transport logs.

## Validation

Static validation:

```bash
python3 -m py_compile cin7-core-live-data/scripts/cin7_core_live_mcp.py
```

Manual validation after configuring credentials:

1. Start the server in `stdio` mode from a client that supports MCP.
2. Ask for a known SKU cost.
3. Ask for product availability for a known SKU and location.
4. Ask for a recent product sales quantity with a narrow date range.
5. Ask for a recent product purchase quantity with a narrow date range.
6. Confirm the answer reports the date field, line source, simple-purchase limitation, and any truncation.
