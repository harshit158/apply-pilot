from typing import TypedDict
from pydantic import BaseModel, Field
from typing import Annotated
from operator import add
from langchain_core.tools.structured import StructuredTool
from langgraph.graph.message import add_messages
from src.agents.commons.models import InputField


class InputFields(BaseModel):
    fields: list[InputField] = Field(
        ..., description="List of input fields identified for job application"
    )


class ApplyButton(BaseModel):
    ref: str | None = Field(
        ...,
        description="Unique reference or identifier for the apply button. If not found, return None",
    )
    reason: str = Field(..., description="Reason why this button is the apply button")


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    job_url: str
    page_trees: Annotated[
        list[dict], add
    ]  # List of page trees extracted at each step of the workflow
    is_apply_button_present: ApplyButton
    input_fields: Annotated[list[InputField], ...]

    # playwright tools
    playwright_tools: Annotated[list[StructuredTool], ...]
    tool_name_to_tool_mapping: Annotated[
        dict[str, StructuredTool], ...
    ]  # mapping from tool name to tool instance
