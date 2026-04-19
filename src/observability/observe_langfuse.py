from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from src.settings import settings

langfuse = Langfuse(
    secret_key=settings.langfuse_secret_key,
    public_key=settings.langfuse_public_key,
    host=settings.langfuse_host,
)


def get_langfuse_handler():
    """Returns a Langfuse CallbackHandler for Langchain / Langgraph to enable tracing."""
    return CallbackHandler()
