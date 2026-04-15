import json
from typing import Annotated, Any, Literal
from xml.parsers.expat import model
from langchain_mcp_adapters import client
from langchain_openai import ChatOpenAI, tools
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import ToolNode, tools_condition
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from sqlalchemy import text
from operator import add
from enum import Enum
from langchain.agents import create_agent
import asyncio

from src.utils import extract_yml_path, read_yml_file
from src.playwright_mcp_client import PlaywrightMCPClient
from src.llm_providers import llm_ollama, llm_openai

class InputType(str, Enum):
    TEXTBOX = "textbox"
    BUTTON = "button"
    UPLOAD = "upload"
    COMBOBOX = "combobox"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    SUBMIT_BUTTON = "submit_button"

class InputField(BaseModel):
    text: str = Field(..., description="Text to analyze for apply button")
    ref: str = Field(..., description="Unique reference or identifier for the input field. If not found, return None")
    type: InputType = Field(..., description="Type of the input field (e.g., textbox, button, combobox, radio, checkbox, submit_button)")
    reason: str = Field(..., description="Reason why this is an input field for job application and it's correct ref value")

class InputFields(BaseModel):
    fields: list[InputField] = Field(..., description="List of input fields identified for job application")
    
class ApplyButton(BaseModel):
    ref: str | None = Field(..., description="Unique reference or identifier for the apply button. If not found, return None")
    reason: str = Field(..., description="Reason why this button is the apply button")
            
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    page_trees: Annotated[list[dict], add] # List of page trees extracted at each step of the workflow
    is_apply_button_present: ApplyButton
    input_fields: Annotated[list[InputField], ...]
    
class JobApplicationAgent:
    def __init__(self, mcp_client: PlaywrightMCPClient, llm, url: str):
        self.mcp_client = mcp_client
        self.llm = llm
        self.llm_with_tools = None
        self.url = url
    
    async def _node_call_model(self, state: AgentState):
        # check if last message was a tool message and if so, extract the yml path and add it to the state
        if not state["messages"]:
            state["messages"].append(SystemMessage(content="You are a helpful web browsing agent that can assist with various tasks."))
        
        response = await self.llm_with_tools.invoke(state["messages"])
        
        return {"messages": [response]}
    
    async def _node_check_for_apply_button(self, state: AgentState):
        print("Entering Node: Check for Apply Button", "\n", "-"*30)
        
        llm_structured = llm_ollama.with_structured_output(ApplyButton)

        response: ApplyButton = llm_structured.invoke([
            {"role": "system", "content": "You are an intelligent agent that can analyze webpage data to identify the apply button for a job application. Identify the apply button in the following webpage data and explain why it's the apply button. Return None if you cannot find it."},
            {"role": "user", "content": f"Here is the webpage data:\n\n{state['page_trees'][-1]}"}])
        
        print("Result: ", response, "\n\n")
        return {"is_apply_button_present": response}
    
    async def _node_click_on_apply_button(self, state: AgentState):
        print("Entering Node: Click on Apply Button", "\n", "-"*30)
        
        if state["is_apply_button_present"].ref is None:
            print("Apply button not found, skipping this step.\n\n")
            return {}
        
        response = await self.tool_name_to_tool_mapping["browser_click"].ainvoke({"ref": state["is_apply_button_present"].ref})
        text = response[0]["text"]
        snapshot_path, page_tree = self._extract_page_tree(text)
        
        print("Result: Extracted page tree at ", snapshot_path, "\n\n")
        
        state["page_trees"].append(page_tree)
        
        print("Result: Clicked on apply button with ref ", state["is_apply_button_present"].ref, "\n\n")
        return state
    
    def _extract_page_tree(self, text: str | None = None) -> tuple[str, dict]:
        if text:
            snapshot_path = extract_yml_path(text)
            page_tree = read_yml_file(snapshot_path)
        else:
            # invoke tool to get page tree
            snapshot_path = None
            
        return snapshot_path, page_tree
        
    async def _node_navigate_to_url(self, state: AgentState):
        print("Entering Node: Navigate to URL", "\n", "-"*30)
        
        response = await self.tool_name_to_tool_mapping["browser_navigate"].ainvoke({"url": self.url})
        text = response[0]["text"]
        
        snapshot_path, page_tree = self._extract_page_tree(text)
        
        print("Result: Extracted page tree at ", snapshot_path, "\n\n")
        
        return {"page_trees": [page_tree]}
    
    async def _node_extract_fields(self, state: AgentState):
        print("Entering Node: Extract Input Fields", "\n", "-"*30)
        
        llm_structured = llm_openai.with_structured_output(InputFields)

        response = llm_structured.invoke([
            {"role": "system", "content": """You are an intelligent agent that can analyze job application webpage data to identify the input fields that need to be filled for a successful application. 
            ## Instructions:
            - Identify the input fields - their text, ref values, type and reason on why do you think they are the correct values.
            - Also identify fields that need to be uploaded with a file and their corresponding ref values and give reason on why do you think they are the correct values."""},
            {"role": "user", "content": f"Here is the webpage data:\n\n{state['page_trees'][-1]}"}])
        
        fields = response.fields
        print("Result: Extracted input fields: ", fields, "\n\n")
        
        return {"input_fields": fields}
    
    async def _single_field_agent(self, field: InputField, state: AgentState):
        # This agent will take in the field to be filled and the current page tree and will return the actions to be taken to fill that field
        print(f"Entering Single Field Agent for field: {field.text} of type {field.type}", "\n", "-"*30)
        
        print("Filling field: ", field.text)
        
        if field.type in [InputType.UPLOAD, InputType.SUBMIT_BUTTON]:
            print("Skipping")
            return
        
        agent = create_agent(
            llm_ollama,
            system_prompt="""You are a helpful web browsing agent that specializes in using the Playwright tools and helps in filling job applications. Use dummy data to fill the fields. For file uploads, just mention the file name that you want to upload. Always use the ref value to identify the field on which you want to perform the action""",
            tools=self.playwright_tools
        )
        
        field_data = json.dumps(field.model_dump())
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": r"""You are given field details in the form of text, ref and type. Your task is to analyze the current webpage data and figure out how to fill this field using the Playwright tools. 
                           Here is the field data: """ + field_data}]
            }
        )
        
        print(response)
    
    async def _node_fill_fields(self, state: AgentState):
        print("Entering Node: Fill Input Fields", "\n", "-"*30)

        fields = state["input_fields"]  # assuming this exists

        # Create coroutines (DO NOT await yet)
        tasks = [
            self._single_field_agent(field, state)
            for field in fields
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Optional: handle errors
        for field, result in zip(fields, results):
            if isinstance(result, Exception):
                print(f"Error processing field {field.text}: {result}")

        return state
        

    def _build_graph(self):
        # Build the Graph
        workflow = StateGraph(AgentState)

        # Add our two primary nodes
        workflow.add_node("navigate_to_url", self._node_navigate_to_url)
        workflow.add_node("check_for_apply_button", self._node_check_for_apply_button)
        workflow.add_node("route_to_apply_button", self._node_click_on_apply_button)
        workflow.add_node("extract_fields", self._node_extract_fields)
        workflow.add_node("fill_fields", self._node_fill_fields)
        workflow.add_node("call_model", self._node_call_model)
        workflow.add_node("tools", ToolNode(self.playwright_tools))

        # Set entry point
        workflow.add_edge(START, "navigate_to_url")
        workflow.add_edge("navigate_to_url", "check_for_apply_button")
        workflow.add_edge("check_for_apply_button", "route_to_apply_button")
        workflow.add_edge("route_to_apply_button", "extract_fields")
        workflow.add_edge("extract_fields", "fill_fields")
        workflow.add_edge("fill_fields", END)

        # Define the logic: 
        # If the agent wants to call a tool, go to 'tools'.
        # Otherwise, finish at END.
        # workflow.add_conditional_edges(
        #     "agent",
        #     tools_condition, # This prebuilt function checks if tool_calls exist
        # )

        # After tools are executed, always go back to the agent to summarize
        # workflow.add_edge("tools", "agent")

        # 5. Compile and Run
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
            self.tool_name_to_tool_mapping = {tool.name: tool for tool in self.playwright_tools}

            # 2. Set up the LLM and bind tools
            # The model needs to know which tools it is allowed to "call"
            self.llm_with_tools = self.llm.bind_tools(self.playwright_tools)

            self.graph = self._build_graph()
            
            # Test the agent
            # inputs = {"messages": [("user", f"Go to {self.url} and apply for the job using ref id: f1e100")]}
            inputs = {"url": self.url}
            async for chunk in self.graph.astream(inputs, stream_mode="values"):
                if len(chunk["messages"])>0:
                    chunk["messages"][-1].pretty_print()