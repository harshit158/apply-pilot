from src.agents.job_agent.models import AgentState, ApplyButton
from src.llm_providers import llm_ollama


async def check_for_apply_button(state: AgentState):
    print("Entering Node: Check for Apply Button", "\n", "-" * 30)

    llm_structured = llm_ollama.with_structured_output(ApplyButton)

    response: ApplyButton = llm_structured.invoke(
        [
            {
                "role": "system",
                "content": "You are an intelligent agent that can analyze webpage data to identify the apply button for a job application. Identify the apply button in the following webpage data and explain why it's the apply button. Return None if you cannot find it.",
            },
            {
                "role": "user",
                "content": f"Here is the webpage data:\n\n{state['page_trees'][-1]}",
            },
        ]
    )  # type: ignore

    print("Result: ", response, "\n\n")
    return {"is_apply_button_present": response}
