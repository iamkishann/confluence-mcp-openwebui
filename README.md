# MCP Atlassian

![PyPI Version](https://img.shields.io/pypi/v/mcp-atlassian)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mcp-atlassian)
![PePy - Total Downloads](https://static.pepy.tech/personalized-badge/mcp-atlassian?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Total%20Downloads)
[![Run Tests](https://github.com/sooperset/mcp-atlassian/actions/workflows/tests.yml/badge.svg)](https://github.com/sooperset/mcp-atlassian/actions/workflows/tests.yml)
![License](https://img.shields.io/github/license/sooperset/mcp-atlassian)
[![Docs](https://img.shields.io/badge/docs-mintlify-blue)](https://mcp-atlassian.soomiles.com)

Model Context Protocol (MCP) server for Atlassian products (Confluence and Jira). Supports both Cloud and Server/Data Center deployments.

https://github.com/user-attachments/assets/35303504-14c6-4ae4-913b-7c25ea511c3e

<details>
<summary>Confluence Demo</summary>

https://github.com/user-attachments/assets/7fe9c488-ad0c-4876-9b54-120b666bb785

</details>

## Quick Start

### 1. Get Your API Token

Go to https://id.atlassian.com/manage-profile/security/api-tokens and create a token.

> For Server/Data Center, use a Personal Access Token instead. See [Authentication](https://mcp-atlassian.soomiles.com/docs/authentication).

### 2. Run It With Open WebUI

Use MCP Atlassian as a Streamable HTTP service and connect it to an Open WebUI container:

```yaml
services:
  mcp-atlassian:
    image: ghcr.io/sooperset/mcp-atlassian:latest
    ports:
      - "9000:8000"
    environment:
      TRANSPORT: streamable-http
      HOST: 0.0.0.0
      PORT: 8000
      READ_ONLY_MODE: "true"
      TOOLSETS: confluence_pages,confluence_comments,confluence_attachments
      CONFLUENCE_URL: https://your-company.atlassian.net/wiki
      CONFLUENCE_USERNAME: your.email@company.com
      CONFLUENCE_API_TOKEN: your_api_token
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      WEBUI_SECRET_KEY: change-me-before-production
    volumes:
      - open-webui:/app/backend/data
    depends_on:
      - mcp-atlassian
    restart: unless-stopped

volumes:
  open-webui:
```

Then in Open WebUI, add an MCP server with the URL `http://mcp-atlassian:8000/mcp`.

If you only see an OpenAPI-focused "Manage Tool Servers" screen, use the **Import JSON** action in that modal and paste:

```json
[
  {
    "type": "mcp",
    "url": "http://mcp-atlassian:8000/mcp",
    "spec_type": "url",
    "spec": "",
    "path": "openapi.json",
    "auth_type": "none",
    "key": "",
    "info": {
      "id": "confluence-mcp",
      "name": "Confluence MCP Atlassian",
      "description": "Confluence tools exposed by MCP Atlassian over Streamable HTTP"
    }
  }
]
```

Use `http://localhost:9000/mcp` only for host-side testing. From inside the Open WebUI container network, the correct URL is `http://mcp-atlassian:8000/mcp`.

If your Open WebUI instance cannot add MCP connections directly, use the Workspace Tool bridge script:

- Script path: `scripts/openwebui/mcp_atlassian_workspace_tool.py`
- In Open WebUI: **Workspace** -> **Tools** -> **Import** -> paste the script.
- Enable the tool for your model/chat, then call:
  - `list_mcp_tools()`
  - `call_mcp_tool(tool_name, arguments_json)`

This tool forwards calls to MCP Atlassian at `http://mcp-atlassian:8000/mcp`.

Ready-to-run files are included in the repo:

- `docker-compose.open-webui.yml`
- `.env.open-webui.dc.example`

> **Server/Data Center users**: Use `CONFLUENCE_PERSONAL_TOKEN` instead of `CONFLUENCE_USERNAME` + `CONFLUENCE_API_TOKEN`. See [Authentication](https://mcp-atlassian.soomiles.com/docs/authentication) for details.

> For Cursor, VS Code, and other stdio clients, see [Installation](https://mcp-atlassian.soomiles.com/docs/installation) and [Configuration](https://mcp-atlassian.soomiles.com/docs/configuration).

### 3. Start Using

Ask your AI assistant to:
- **"Find issues assigned to me in PROJ project"**
- **"Search Confluence for onboarding docs"**
- **"Create a bug ticket for the login issue"**
- **"Update the status of PROJ-123 to Done"**

## Documentation

Full documentation is available at **[mcp-atlassian.soomiles.com](https://mcp-atlassian.soomiles.com)**.

Documentation is also available in [llms.txt format](https://llmstxt.org/), which LLMs can consume easily:
- [`llms.txt`](https://mcp-atlassian.soomiles.com/llms.txt) — documentation sitemap
- [`llms-full.txt`](https://mcp-atlassian.soomiles.com/llms-full.txt) — complete documentation

| Topic | Description |
|-------|-------------|
| [Installation](https://mcp-atlassian.soomiles.com/docs/installation) | uvx, Docker, pip, from source |
| [Authentication](https://mcp-atlassian.soomiles.com/docs/authentication) | API tokens, PAT, OAuth 2.0 |
| [Configuration](https://mcp-atlassian.soomiles.com/docs/configuration) | Open WebUI, stdio clients, environment variables |
| [Open WebUI Guide](https://mcp-atlassian.soomiles.com/docs/guides/open-webui) | Confluence-only container setup for Open WebUI |
| [HTTP Transport](https://mcp-atlassian.soomiles.com/docs/http-transport) | SSE, streamable-http, multi-user |
| [Tools Reference](https://mcp-atlassian.soomiles.com/docs/tools-reference) | All Jira & Confluence tools |
| [Troubleshooting](https://mcp-atlassian.soomiles.com/docs/troubleshooting) | Common issues & debugging |

## Compatibility

| Product | Deployment | Support |
|---------|------------|---------|
| Confluence | Cloud | Fully supported |
| Confluence | Server/Data Center | Supported (v6.0+) |
| Jira | Cloud | Fully supported |
| Jira | Server/Data Center | Supported (v8.14+) |

## Key Tools

| Jira | Confluence |
|------|------------|
| `jira_search` - Search with JQL | `confluence_search` - Search with CQL |
| `jira_get_issue` - Get issue details | `confluence_get_page` - Get page content |
| `jira_create_issue` - Create issues | `confluence_create_page` - Create pages |
| `jira_update_issue` - Update issues | `confluence_update_page` - Update pages |
| `jira_transition_issue` - Change status | `confluence_add_comment` - Add comments |

**72 tools total** — See [Tools Reference](https://mcp-atlassian.soomiles.com/docs/tools-reference) for the complete list.

## Security

Never share API tokens. Keep `.env` files secure. See [SECURITY.md](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

## License

MIT - See [LICENSE](LICENSE). Not an official Atlassian product.
