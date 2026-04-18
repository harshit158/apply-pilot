from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

load_dotenv(dotenv_path="/Users/harshit/Documents/Projects/foundry/.env", override=True)

llm_ollama = ChatOllama(
    name="gemma4:e4b",
    model="gemma4:e4b",
    temperature=0.1,
    reasoning=True,
)

llm_ollama_gemma = ChatOllama(
    name="gemma4:e4b",
    model="gemma4:e4b",
    temperature=0.1,
    reasoning=True,
)

llm_openai = ChatOpenAI(
    name="gpt-5-nano",
    model="gpt-5-nano",
    temperature=0.3,
)
