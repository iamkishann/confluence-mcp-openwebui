"""
import this in the openwebui tools
title: MCP Atlassian Bridge Tool
author: mcp-atlassian
version: 0.1.0
description: Open WebUI Workspace Tool that forwards Confluence/Jira searches to an MCP Atlassian streamable-http endpoint.
requirements: httpx
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        mcp_url: str = Field(
            default="http://mcp-atlassian:8000/mcp",
            description="MCP Atlassian Streamable HTTP endpoint",
        )

    def __init__(self) -> None:
        self.valves = self.Valves()

    async def _mcp_request(
        self,
        method: str,
        params: dict[str, Any],
        request_id: int,
        session_id: str,
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id,
        }

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.valves.mcp_url, headers=headers, json=payload)
            resp.raise_for_status()
            return self._extract_jsonrpc(resp.text)

    async def _initialize_session(self) -> str:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "open-webui-workspace-tool",
                    "version": "0.1.0",
                },
            },
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            init_resp = await client.post(
                self.valves.mcp_url,
                headers=headers,
                json=init_payload,
            )
            init_resp.raise_for_status()

        session_id = init_resp.headers.get("mcp-session-id")
        if not session_id:
            raise ValueError("Missing mcp-session-id from initialize response")
        return session_id

    @staticmethod
    def _extract_jsonrpc(payload_text: str) -> dict[str, Any]:
        """Parse JSON-RPC result from SSE or JSON response payload."""
        # Streamable HTTP can return event-stream formatted payloads.
        for line in payload_text.splitlines():
            if line.startswith("data:"):
                data = line[len("data:") :].strip()
                if not data:
                    continue
                return json.loads(data)

        # Fallback: plain JSON response body.
        return json.loads(payload_text)

    @staticmethod
    def _format_tool_result(result: dict[str, Any]) -> str:
        if "error" in result:
            return f"MCP error: {json.dumps(result['error'])}"

        content = result.get("result", {}).get("content", [])
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))

        if text_parts:
            return "\n\n".join(part for part in text_parts if part)

        return json.dumps(result.get("result", {}), indent=2)

    async def list_mcp_tools(self) -> str:
        """
        List all tools exposed by the MCP Atlassian server.
        """
        try:
            session_id = await self._initialize_session()
            result = await self._mcp_request("tools/list", {}, 2, session_id)
            if "error" in result:
                return f"MCP error: {json.dumps(result['error'])}"
            return json.dumps(result.get("result", {}), indent=2)
        except Exception as exc:  # noqa: BLE001
            return f"MCP bridge error: {exc}"

    async def call_mcp_tool(self, tool_name: str, arguments_json: str = "{}") -> str:
        """
        Call any MCP Atlassian tool by name.

        :param tool_name: MCP tool name such as jira_search, jira_get_issue,
            confluence_search, confluence_get_page.
        :param arguments_json: JSON object string for the tool arguments.
            Example: {"jql":"project=ABC","limit":10}
        """
        try:
            arguments = json.loads(arguments_json)
            if not isinstance(arguments, dict):
                return "MCP bridge error: arguments_json must decode to a JSON object"

            session_id = await self._initialize_session()
            result = await self._mcp_request(
                "tools/call",
                {
                    "name": tool_name,
                    "arguments": arguments,
                },
                2,
                session_id,
            )
            return self._format_tool_result(result)
        except json.JSONDecodeError as exc:
            return f"MCP bridge error: invalid arguments_json ({exc})"
        except Exception as exc:  # noqa: BLE001
            return f"MCP bridge error: {exc}"
