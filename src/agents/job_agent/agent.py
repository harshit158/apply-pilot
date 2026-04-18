from langgraph.graph import StateGraph, START, END
from langchain_mcp_adapters.tools import load_mcp_tools

from src.playwright_mcp_client import PlaywrightMCPClient

from src.agents.job_agent.models import AgentState

# import nodes
from src.agents.job_agent.nodes.check_for_apply_button import check_for_apply_button
from src.agents.job_agent.nodes.navigate_to_url import navigate_to_url
from src.agents.job_agent.nodes.click_on_apply_button import click_on_apply_button
from src.agents.job_agent.nodes.extract_fields import extract_fields
from src.agents.job_agent.nodes.fill_fields import fill_fields


class JobAgent:
    def __init__(self, mcp_client: PlaywrightMCPClient, llm, url: str):
        self.mcp_client = mcp_client
        self.llm = llm
        self.llm_with_tools = None
        self.url = url

    async def _node_init(self, state: AgentState):
        """ "Populate playwright tools in the state so that they can be used by other nodes"""

        return {
            "job_url": self.url,
            "playwright_tools": self.playwright_tools,
            "tool_name_to_tool_mapping": self.tool_name_to_tool_mapping,
        }

    async def _build_graph(self):
        # Build the Graph
        workflow = StateGraph(AgentState)

        # Add our two primary nodes
        workflow.add_node("init", self._node_init)
        workflow.add_node("navigate_to_url", navigate_to_url)
        workflow.add_node("check_for_apply_button", check_for_apply_button)
        workflow.add_node("route_to_apply_button", click_on_apply_button)
        workflow.add_node("extract_fields", extract_fields)
        workflow.add_node("fill_fields", fill_fields)

        # Set entry point
        workflow.add_edge(START, "init")
        workflow.add_edge("init", "navigate_to_url")
        workflow.add_edge("navigate_to_url", "check_for_apply_button")
        workflow.add_edge("check_for_apply_button", "route_to_apply_button")
        workflow.add_edge("route_to_apply_button", "extract_fields")
        workflow.add_edge("extract_fields", "fill_fields")
        workflow.add_edge("fill_fields", END)

        # Compile and Run
        graph = workflow.compile()

        return graph

    def print_config(self):
        print("Agent Configuration:")
        print("-" * 30)
        print(f"LLM: {self.llm.name}")
        print(f"URL: {self.url}")
        print("-" * 30, "\n\n")

    async def invoke(self):
        # print config
        self.print_config()

        # self.tool_name_to_tool_mapping = await self.mcp_client.get_tool_name_to_tool_mapping(mode="headless")
        self.client = await self.mcp_client.get_client("headful")
        async with self.client.session("playwright") as session:
            # playwright_tools = await client.get_tools()
            self.playwright_tools = await load_mcp_tools(session)
            self.tool_name_to_tool_mapping = {
                tool.name: tool for tool in self.playwright_tools
            }

            # 2. Set up the LLM and bind tools
            # The model needs to know which tools it is allowed to "call"
            self.llm_with_tools = self.llm.bind_tools(self.playwright_tools)

            self.graph = await self._build_graph()

            # Test the agent
            # inputs = {"messages": [("user", f"Go to {self.url} and apply for the job using ref id: f1e100")]}
            inputs = {"url": self.url}
            async for chunk in self.graph.astream(inputs, stream_mode="values"):
                if len(chunk["messages"]) > 0:
                    chunk["messages"][-1].pretty_print()
