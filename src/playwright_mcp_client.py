from langchain_mcp_adapters.client import MultiServerMCPClient  
    
class PlaywrightMCPClient():
    def __init__(self):
        self._headless_client = None
        self._headful_client = None

    async def headless_client(self):
        if self._headless_client is None:
            self._headless_client = await self._get_client("headless")
        return self._headless_client

    async def headful_client(self):
        if self._headful_client is None:
            self._headful_client = await self._get_client("headful")
        return self._headful_client
    
    async def _get_client(self, mode):
        if mode == "headless":
            args = ["@playwright/mcp@latest", "--extension", "--headless"]
        elif mode == "headful":
            args = ["@playwright/mcp@latest", "--extension"]
            
        client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": args,
            "transport": "stdio",
            "env": {
                "PLAYWRIGHT_MCP_EXTENSION_TOKEN":"L-GDSJHJCPuarXeH8l1TB3LMnQBb7MSE9swh9REp3nU",
                "PLAYWRIGHT_MCP_OUTPUT_DIR": "src/assets/playwright_mcp_output",
            }
            }
        })
        
        return client

    async def get_client(self, mode):
        if mode == "headless":
            return await self.headless_client()
        elif mode == "headful":
            return await self.headful_client()
        else:
            raise ValueError("Invalid mode. Use 'headless' or 'headful'.")
        
    async def get_tools(self, mode):
        client = await self.get_client(mode)
        tools = await client.get_tools()
        return tools

    async def get_tool_name_to_tool_mapping(self, mode) -> dict:
        tools = await self.get_tools(mode)
        tool_name_to_tool = {tool.name: tool for tool in tools}
        return tool_name_to_tool