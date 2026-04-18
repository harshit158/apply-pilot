from src.agents.job_agent.models import AgentState
from src.utils import extract_page_tree


async def navigate_to_url(state: AgentState):
    print("Entering Node: Navigate to URL", "\n", "-" * 30)

    response = await state["tool_name_to_tool_mapping"]["browser_navigate"].ainvoke(
        {"url": state["job_url"]}
    )
    text = response[0]["text"]

    snapshot_path, page_tree = extract_page_tree(text)

    print("Result: Extracted page tree at ", snapshot_path, "\n\n")

    return {"page_trees": [page_tree]}
