import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from devtools_search import InfraiClient, SearchRequest, search_developer_tools


class FakeClient:
    def embed(self, text):
        assert text == "release rollback diagnostics"
        return [0.1, 0.2]

    def query(self, collection, embedding, top_k):
        assert collection == "developer-tools"
        return [{"metadata": {"title": "Rollback guide", "url": "/rollback", "kind": "release"}, "score": 0.7}]

    def rerank(self, query, candidates, top_k):
        return [{**candidates[0], "relevance_score": 0.99}]


def test_search_hands_off_vector_results_to_reranker():
    hits = search_developer_tools(FakeClient(), SearchRequest("release rollback diagnostics"))
    assert hits == [type(hits[0])("Rollback guide", "/rollback", 0.99, "release")]


def test_client_accepts_list_capability_responses():
    client = InfraiClient("test-key")
    matches = [{"metadata": {"title": "Rollback guide"}, "score": 0.7}]
    ranked = [{**matches[0], "relevance_score": 0.99}]
    responses = iter([{"data": matches}, {"data": ranked}])
    client._post = lambda path, payload: next(responses)

    assert client.query("developer-tools", [0.1, 0.2], 10) == matches
    assert client.rerank("rollback", matches, 5) == ranked
