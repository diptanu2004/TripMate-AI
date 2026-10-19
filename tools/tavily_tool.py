from tavily import TavilyClient
import os
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

API_KEY = os.getenv("TAVILY_API_KEY")

_client = None


def get_client():
    global _client

    if _client is None:
        _client = TavilyClient(api_key = API_KEY)

    return _client


@tool
def tavily_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for current travel information such as attractions, visa
    rules, weather, local costs and safety advice.

    Pass a focused natural language query, e.g. "best tourist attractions in
    Paris" or "Japan visa requirements for Bangladeshi citizens". Returns a
    numbered list of results with titles, URLs and short snippets.
    """
    if not API_KEY:
        return "Search API error: TAVILY_API_KEY is missing from the .env file."

    try:
        response = get_client().search(
            query = query,
            max_results = max_results
        )
    except Exception as e:
        return f"Search API request failed: {e}"

    results = []

    for i, r in enumerate(response.get("results") or [], 1):
        title = r.get("title") or "Unknown"
        url = r.get("url") or "Unknown"
        snippet = (r.get("content") or "No snippet available.").strip()

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(' ', 1)[0] + "..."

        results.append(f"{i}. **{title}**\nURL: {url}\nSnippet: {snippet}\n")

    if not results:
        return f"No search results found for '{query}'."

    return "\n".join(results)
