import asyncio
from src.agents.job_agent.models import AgentState
from src.agents.field_agent.agent import FieldAgent


async def fill_fields(state: AgentState):
    print("Entering Node: Fill Input Fields", "\n", "-" * 30)

    fields = state["input_fields"]  # assuming this exists

    # Create coroutines (DO NOT await yet)
    tasks = [FieldAgent(field, 
                        state["playwright_tools"], 
                        state["tool_name_to_tool_mapping"]).invoke() for field in fields]

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Optional: handle errors
    for field, result in zip(fields, results):
        if isinstance(result, Exception):
            print(f"Error processing field {field.text}: {result}")

    return state
