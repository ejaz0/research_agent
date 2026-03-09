# agent.py
from tools import search_web, fetch_url, summarize

def research_agent(user_query):
    print(f"User asked: {user_query}\n")

    # Step 1: Search Web
    urls = search_web(user_query, num_results=3)
    print("Found URLs:")
    for u in urls:
        print("-", u)
    print()

    # Step 2: Fetch content
    contents = []
    for url in urls:
        print(f"Fetching: {url}")
        text = fetch_url(url)
        contents.append(text[:800])  # truncate to avoid huge requests
    print("\nFetched content from pages.\n")

    # Step 3: Summarize each page
    summaries = []
    for content in contents:
        summary = summarize(content)
        summaries.append(summary)
    print("Summaries ready.\n")

    # Step 4: Combine summaries
    final_summary = "\n---\n".join(summaries)
    return final_summary