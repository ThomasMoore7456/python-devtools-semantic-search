import argparse
import json
from devtools_search import InfraiClient, SearchRequest, search_developer_tools


def main() -> None:
    parser = argparse.ArgumentParser(description="Search build, release, and diagnostics notes")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    hits = search_developer_tools(InfraiClient(), SearchRequest(args.query, args.top_k))
    print(json.dumps([hit.__dict__ for hit in hits], indent=2))


if __name__ == "__main__":
    main()
