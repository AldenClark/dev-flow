#!/usr/bin/env python3
"""Serve one deterministic, network-free MCP tool for Dev Flow Bench fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def response(request_id: Any, result: dict[str, Any]) -> None:
    sys.stdout.write(
        json.dumps(
            {"jsonrpc": "2.0", "id": request_id, "result": result},
            separators=(",", ":"),
        )
        + "\n"
    )
    sys.stdout.flush()


def serve(tool_name: str) -> int:
    for line in sys.stdin:
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(request, dict):
            continue
        method = request.get("method")
        request_id = request.get("id")
        if method == "initialize" and request_id is not None:
            params = request.get("params")
            protocol_version = (
                params.get("protocolVersion", "2025-06-18")
                if isinstance(params, dict)
                else "2025-06-18"
            )
            response(
                request_id,
                {
                    "protocolVersion": protocol_version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "dev-flow-bench-fixture",
                        "version": "1",
                    },
                },
            )
        elif method == "tools/list" and request_id is not None:
            response(
                request_id,
                {
                    "tools": [
                        {
                            "name": tool_name,
                            "description": "Deterministic read-only benchmark fixture tool.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                            "annotations": {
                                "readOnlyHint": True,
                                "openWorldHint": False,
                                "destructiveHint": False,
                            },
                        }
                    ]
                },
            )
        elif method == "tools/call" and request_id is not None:
            params = request.get("params")
            requested = params.get("name") if isinstance(params, dict) else None
            if requested != tool_name:
                response(
                    request_id,
                    {
                        "content": [{"type": "text", "text": "unknown fixture tool"}],
                        "isError": True,
                    },
                )
            else:
                response(
                    request_id,
                    {
                        "content": [
                            {"type": "text", "text": f"runner-fixture:pass:{tool_name}"}
                        ],
                        "isError": False,
                    },
                )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(serve(arguments.tool))
