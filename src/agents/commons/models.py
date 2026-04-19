from enum import Enum

from pydantic import BaseModel, Field


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
    ref: str = Field(
        ...,
        description="Unique reference or identifier for the input field. If not found, return None",
    )
    type: InputType = Field(
        ...,
        description="Type of the input field (e.g., textbox, button, combobox, radio, checkbox, submit_button)",
    )
    reason: str = Field(
        ...,
        description="Reason why this is an input field for job application and it's correct ref value",
    )
