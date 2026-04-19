from typing import Annotated, TypedDict

from langchain_core.tools.structured import StructuredTool
from langgraph.graph.message import add_messages

from src.agents.commons.models import InputField


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    input_field: Annotated[InputField, ...]

    # playwright tools
    playwright_tools: Annotated[list[StructuredTool], ...]
    tool_name_to_tool_mapping: Annotated[dict[str, StructuredTool], ...]  # mapping from tool name to tool instance
