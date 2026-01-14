# Frappe MCP Server Setup

## Overview

The Frappe MCP (Model Context Protocol) server provides AI assistants with direct access to your Frappe/ERPNext database and DocTypes. This allows AI tools to query, search, and retrieve information from your KoraFlow installation.

## Configuration

The MCP server has been configured in Cursor IDE at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "frappe": {
      "command": "/Users/tjaartprinsloo/Documents/KoraFlow/bench/env/bin/python3",
      "args": [
        "/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps/koraflow_core/koraflow_core/frappe_mcp.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/tjaartprinsloo/Documents/KoraFlow/bench/apps"
      }
    }
  }
}
```

## Available Tools

The Frappe MCP server exposes the following tools:

### 1. `ping() -> str`
Check if the server is running and connected to Frappe DB.
- Returns: Connection status message

### 2. `get_installed_apps() -> list[str]`
Get list of installed apps on the current site.
- Returns: List of installed app names

### 3. `get_doctype_meta(doctype: str) -> dict`
Get metadata (fields, options) for a specific DocType.
- Parameters:
  - `doctype`: The DocType name (e.g., "Patient", "Sales Order")
- Returns: Dictionary with doctype info, module, fields, etc.

### 4. `get_document(doctype: str, name: str) -> dict`
Fetch a specific document by name.
- Parameters:
  - `doctype`: The DocType name
  - `name`: The document name/ID
- Returns: Document data as dictionary

### 5. `search_docs(doctype: str, txt: str) -> list[dict]`
Search for documents using a text query.
- Parameters:
  - `doctype`: The DocType to search
  - `txt`: Text to search for in document names
- Returns: List of matching documents (limited to 10)

## Usage

Once configured, the MCP server will automatically start when Cursor IDE launches. The AI assistant can then use these tools to:

- Query your Frappe database
- Get DocType metadata
- Search for documents
- Retrieve specific records

## Testing

To test the server manually:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow/bench
env/bin/python3 apps/koraflow_core/koraflow_core/frappe_mcp.py
```

The server runs over stdio transport, so it will wait for MCP protocol messages.

## Site Configuration

The server connects to the `koraflow-site` Frappe site by default. To change this, modify the `init_frappe_site()` function in `frappe_mcp.py`.

## Troubleshooting

1. **"Frappe module not found"**: Ensure you're running from the bench environment with Frappe installed.

2. **Connection errors**: Verify that:
   - The Frappe site exists in `bench/sites/koraflow-site`
   - Database is accessible
   - Site is properly configured

3. **MCP server not starting**: Check:
   - Python path is correct in `mcp.json`
   - Script path is correct
   - PYTHONPATH environment variable is set

## File Location

- MCP Server Script: `bench/apps/koraflow_core/koraflow_core/frappe_mcp.py`
- MCP Configuration: `~/.cursor/mcp.json`
