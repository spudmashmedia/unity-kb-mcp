# Setup Tooling

## LM Studio

In the Developer Tab, edit the **mcp.json**

```json
{
  "mcpServers": {
    "unity_docs": {
      "url": "http://127.0.0.1:8002/mcp"
    }
  }
}
```

When saved, returning back to Chat tab you should see on the right sidebar under Integrations the **mcp/unity_docs | Tools | search_unity_api**:

![LM Studio](/docs/img/lm_studio_tool_active.png)

## OpenCode
To get the tool operational with OpenCode, add the following to your **opencode.config**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "unity-docs": {
      "type": "remote",
      "url": "http://host.docker.internal:8002/mcp",
      "enable": true
    }
  }
}

```

![OpenCode](/docs/img/opencode_tool_active.png)

---
Spudmash Media [-] 2026

