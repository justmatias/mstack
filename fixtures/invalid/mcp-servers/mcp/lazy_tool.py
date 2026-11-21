from fastmcp import FastMCP

mcp = FastMCP("foo")


@mcp.tool()
def list_items():
    return []


def run_mcp_server():
    server = FastMCP("foo")
    server.add_tool(tool=list_items)
    server.run()
