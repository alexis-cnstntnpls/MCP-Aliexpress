import json
import subprocess
import sys

# Test stdio JSON-RPC interaction with the MCP server
cmd = [
    "/home/alexis/MCP-AliExpress/.venv/bin/python",
    "-m",
    "aliexpress_mcp.server",
    "--transport",
    "stdio",
]

env = {"PYTHONPATH": "/home/alexis/MCP-AliExpress/src"}

proc = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env,
)

try:
    # 1. Send initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()

    line = proc.stdout.readline()
    print("Init response:", line.strip())
    init_res = json.loads(line)
    assert init_res.get("result", {}).get("serverInfo", {}).get("name") == "AliExpress FR"

    # Send initialized notification
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()

    # 2. Send tools/list
    list_tools_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    proc.stdin.write(json.dumps(list_tools_req) + "\n")
    proc.stdin.flush()

    line2 = proc.stdout.readline()
    print("\nTools list response received!")
    tools_res = json.loads(line2)
    tools = tools_res.get("result", {}).get("tools", [])
    print(f"Total tools exposed: {len(tools)}")
    for t in tools:
        print(f" - {t.get('name')}: {t.get('description')[:70]}...")

    # 3. Call search_aliexpress_products
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_aliexpress_products",
            "arguments": {
                "query": "raspberry pi",
                "page": 1,
                "sort": "orders",
            },
        },
    }
    print("\nCalling search_aliexpress_products via MCP protocol...")
    proc.stdin.write(json.dumps(call_req) + "\n")
    proc.stdin.flush()

    line3 = proc.stdout.readline()
    call_res = json.loads(line3)
    content = call_res.get("result", {}).get("content", [])
    assert len(content) > 0, "No content returned from tool call"
    data = json.loads(content[0]["text"])
    print(f"Tool call succeeded! Total items found: {data.get('total_results')}")
    if data.get("products"):
        p = data["products"][0]
        print(f"First product: {p.get('title')[:60]}... ({p.get('price_formatted')})")

    print("\n TOUS LES TESTS MCP JSON-RPC SONT PASSÉS AVEC SUCCÈS !")

finally:
    proc.terminate()
    proc.wait(timeout=3)
