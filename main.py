from agent import research_agent

if __name__ == "__main__":
    query = input("Enter your research query: ")
    summary = research_agent(query)
    print("\n=== Agent Final Summary ===\n")
    print(summary)