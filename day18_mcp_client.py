import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\Areesha\\day1-internship\\mcp_test_files"]
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to MCP server!")

            tools = await session.list_tools()
            print("Tools available:", [t.name for t in tools.tools])

            result = await session.call_tool(
                "read_text_file",
                arguments={"path": "C:\\Users\\Areesha\\day1-internship\\mcp_test_files\\notes.txt"}
            )
            print("File content:", result.content[0].text)

asyncio.run(main())