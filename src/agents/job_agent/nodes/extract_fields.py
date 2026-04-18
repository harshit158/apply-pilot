from src.agents.job_agent.models import AgentState, InputFields
from src.llm_providers import llm_openai


async def extract_fields(state: AgentState):
    print("Entering Node: Extract Input Fields", "\n", "-" * 30)

    llm_structured = llm_openai.with_structured_output(InputFields)

    response: InputFields = llm_structured.invoke(
        [
            {
                "role": "system",
                "content": """You are an intelligent agent that can analyze job application webpage data to identify the input fields that need to be filled for a successful application. 
        ## Instructions:
        - Identify the input fields - their text, ref values, type and reason on why do you think they are the correct values.
        - Also identify fields that need to be uploaded with a file and their corresponding ref values and give reason on why do you think they are the correct values.""",
            },
            {
                "role": "user",
                "content": f"Here is the webpage data:\n\n{state['page_trees'][-1]}",
            },
        ]
    )  # type: ignore

    fields = response.fields
    print("Result: Extracted input fields: ", fields, "\n\n")

    return {"input_fields": fields}
