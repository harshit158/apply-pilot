from langgraph.graph import StateGraph, START, END
from src.agents.field_agent.models import AgentState, InputField

# import nodes
from src.agents.field_agent.nodes.fill_field import fill_field


class FieldAgent:
    def __init__(self, input_field: InputField, playwright_tools, tool_name_to_tool_mapping):
        self.input_field = input_field
        self.playwright_tools = playwright_tools
        self.tool_name_to_tool_mapping = tool_name_to_tool_mapping

    def _node_init(self, state: AgentState):
        """ "Populate playwright tools in the state so that they can be used by other nodes"""

        return {
            "playwright_tools": self.playwright_tools,
            "tool_name_to_tool_mapping": self.tool_name_to_tool_mapping,
        }

    async def _build_graph(self):
        # Build the Graph
        workflow = StateGraph(AgentState)

        # Add our two primary nodes
        workflow.add_node("init", self._node_init)
        workflow.add_node("fill_field", fill_field)

        # Set entry point
        workflow.add_edge(START, "init")
        workflow.add_edge("init", "fill_field")
        workflow.add_edge("fill_field", END)

        # Compile and Run
        graph = workflow.compile()

        return graph

    async def invoke(self):
        self.graph = await self._build_graph()

        # stream results
        async for chunk in self.graph.astream(
            {"input_field": self.input_field}, stream_mode="values"
        ):
            print("Chunk from FieldAgent:", chunk)
