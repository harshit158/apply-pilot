import asyncio
import json
from pathlib import Path
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright
from src.playwright_mcp_client import PlaywrightMCPClient
from src.utils import read_yml_file, extract_yml_path

class JobsList(BaseModel):
    job_titles: list[str] = Field(..., description="List of job titles extracted from the LinkedIn jobs search page.")
    
class JobListParser:
    def __init__(self, mcp_client: PlaywrightMCPClient, llm):
        self.mcp_client = mcp_client
        self.llm = llm
        self.linkedin_session_storage_path = Path("src/assets/linkedin_state.json")
        self.playwright_snapshot_dir = Path("src/assets/playwright_mcp_output")

    def extract_job_titles(self, data) -> list[str]:
        titles = []

        def dfs(node):
            if isinstance(node, dict):
                for k, v in node.items():

                    # ✅ DIRECT HIT: text node
                    if k == "text" and isinstance(v, str):
                        if self.is_job_title(v):
                            titles.append(v.strip())

                    dfs(v)

            elif isinstance(node, list):
                for item in node:
                    dfs(item)

        dfs(data)

        # cleanup duplicates while preserving order
        seen = set()
        return [t for t in titles if not (t in seen or seen.add(t))]


    def is_job_title(self, text: str) -> bool:
        text = text.lower()

        # LinkedIn job titles are usually long + contain roles
        keywords = [
            "engineer",
            "scientist",
            "developer",
            "architect",
            "manager",
            "lead",
            "ml",
            "ai",
        ]

        return (
            len(text) > 10 and
            any(k in text for k in keywords)
        )
    
    async def _get_companies_list(self, url: str) -> list[str]:
        tool_name_to_tool = await self.mcp_client.get_tool_name_to_tool_mapping(mode="headless")
        response = await tool_name_to_tool["browser_navigate"].ainvoke({
            "url": url
        })
        
        response_text = response[0]["text"]
        
        snapshot_path = extract_yml_path(response_text)
        if not snapshot_path:
            print("No YML path found in the response text.")
            return []
        
        if snapshot_path:
            yml_data = read_yml_file(snapshot_path)
            print(f"Extracted YML data: {json.dumps(yml_data)[:100]} ...")
        else:
            print("YML path extraction failed.")
            return []
        
        job_titles = self.extract_job_titles(yml_data)
        
        return job_titles
        # print("Invoking LLM to extract job titles from the YML data...")
        # llm_structured = self.llm.with_structured_output(JobsList)
        # llm_response = await llm_structured.ainvoke(f"You are given the accessibility tree of a LinkedIn jobs search page. Extract the list of job titles from the page for using in the Playwright automation: {yml_data}")
        
        # return llm_response.job_titles

    async def parse(self, url: str) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            context = await browser.new_context(storage_state=self.linkedin_session_storage_path)
            page = await context.new_page()

            await page.goto(url)
            
            companies_list = await self._get_companies_list(url)
            print("Total companies extracted: ", len(companies_list))
            
            company_to_apply_url = {}

            for i, company in enumerate(companies_list[:10]):
                print(f"Processing company: {company}")
                
                # click job in left panel
                company = company.replace('(Verified job)', '').strip()  # Clean up job title if it contains quotes
                await page.get_by_role("button",name=company,exact=False).first.click()

                # wait for right panel to load (VERY IMPORTANT)
                await page.wait_for_timeout(2000) 

                try:
                    # 3️⃣ click Apply button in main panel (with robust waits + fallback)
                    async with page.expect_popup(timeout=5000) as popup_info:
                        await page.get_by_role(
                            "link",
                            name="Apply on company website"
                        ).click(timeout=2000)

                    new_tab = await popup_info.value

                    await new_tab.wait_for_load_state()
                    
                    # Full page screenshot
                    await new_tab.screenshot(
                        path=f"src/assets/screenshots/new_tab_{i}.png",
                        full_page=True
                    )

                    print("New tab URL:", new_tab.url)
                    
                    company_to_apply_url[company] = new_tab.url
                except Exception as e:
                    print(f"Error processing {company}: {e}")
                    company_to_apply_url[company] = "Error extracting URL"

            print("Company to Apply URL mapping:")
            for company, url in company_to_apply_url.items():
                print(f"{company}: {url}")
                
            # 4️⃣ keep open for debugging
            await page.wait_for_timeout(10000)
            
            return company_to_apply_url