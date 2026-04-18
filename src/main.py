from src.playwright_mcp_client import PlaywrightMCPClient
from src.llm_providers import llm_ollama
from src.agents.job_agent.agent import JobAgent
import asyncio


async def main(url: str):
    mcp_client = PlaywrightMCPClient()

    # Get a list of all the jobs present on the LinkedIn search page
    # parser = JobListParser(mcp_client, llm_ollama)
    # jobs = await parser.parse(url)

    # Invoke job application agent for each job
    job_url = "https://www.mercor.com/careers/?ashby_jid=e0ba162c-7e0e-4eee-a296-838c8b6e9034&utm_source=Xqz4BKyMEM&src=LinkedIn"
    agent = JobAgent(mcp_client, llm_ollama, job_url)
    await agent.invoke()


if __name__ == "__main__":
    url = "https://www.linkedin.com/jobs/search-results/?keywords=ai%20engineer%20california&origin=JOB_SEARCH_PAGE_JOB_FILTER&referralSearchId=smwl2%2F6GJCko5imqwVXYnA%3D%3D&geoId=102095887&distance=25&f_TPR=r86400"
    asyncio.run(main(url))
