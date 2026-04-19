import json

from langchain.agents import create_agent

from src.agents.commons.models import InputType
from src.agents.field_agent.models import AgentState
from src.llm_providers import llm_ollama


async def fill_field(state: AgentState):
    # This agent will take in the field to be filled and the current page tree and will return the actions to be taken to fill that field
    print(
        f"Entering Single Field Agent for field: {state['input_field'].text} of type {state['input_field'].type}",
        "\n",
        "-" * 30,
    )

    print("Filling field: ", state["input_field"].text)

    if state["input_field"].type in [InputType.UPLOAD, InputType.SUBMIT_BUTTON]:
        print("Skipping")
        return

    agent = create_agent(
        llm_ollama,
        system_prompt="""You are a helpful web browsing agent that specializes in using the Playwright tools and helps in filling job applications. Use dummy data to fill the fields. For file uploads, just mention the file name that you want to upload. Always use the ref value to identify the field on which you want to perform the action""",
        tools=state["playwright_tools"],
    )

    field_data = json.dumps(state["input_field"].model_dump())
    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": r"""You are given field details in the form of text, ref and type. Your task is to analyze the current webpage data and figure out how to fill this field using the Playwright tools.
                        Here is the field data: """
                    + field_data,
                }
            ]
        }
    )

    print(response)
