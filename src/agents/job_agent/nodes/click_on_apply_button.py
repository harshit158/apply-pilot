from src.agents.job_agent.models import AgentState
from src.utils import extract_page_tree


async def click_on_apply_button(state: AgentState):
    print("Entering Node: Click on Apply Button", "\n", "-" * 30)

    if state["is_apply_button_present"].ref is None:
        print("Apply button not found, skipping this step.\n\n")
        return {}

    response = await state["tool_name_to_tool_mapping"]["browser_click"].ainvoke({"ref": state["is_apply_button_present"].ref})
    text = response[0]["text"]
    snapshot_path, page_tree = extract_page_tree(text)

    print("Result: Extracted page tree at ", snapshot_path, "\n\n")

    state["page_trees"].append(page_tree)

    print(
        "Result: Clicked on apply button with ref ",
        state["is_apply_button_present"].ref,
        "\n\n",
    )
    return state
