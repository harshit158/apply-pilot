# expose tool definitions here for easier imports in agent.py
from .check_for_apply_button import check_for_apply_button
from .navigate_to_url import navigate_to_url

__all__ = [
    "navigate_to_url",
    "check_for_apply_button",
]
