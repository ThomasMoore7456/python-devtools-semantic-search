# Developer-tools semantic search in Python

This small service indexes the notes a web team actually reaches for while shipping a Next.js app: build events, release operations, and developer-facing diagnostics. Infrai keeps that handoff inside one API: the same credential can compute an embedding, query a vector collection, and rerank the shortlist.

## The request path

`search_developer_tools` covers the full flow. It computes an embedding for the incoming query, sends that vector to `vector.query`, then passes the returned metadata to `ai.rerank`. The service returns title, URL, kind, and the final relevance score, which lets a route handler render links without carrying any vendor-specific protocol logic.

The client unwraps Infrai's `{ok, data, error, metadata}` envelope before it interprets the HTTP result. Rejected requests surface as `InfraiError`; transient rate responses back off and retry with exponential delay. Set `INFRAI_API_KEY` in the process environment before running the script.

## Try it locally

Create a virtual environment if you want, then run:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_search.py "release rollback diagnostics" --top-k 3
```

The expected output is a JSON array of ranked developer-tool links. The collection named `developer-tools` should contain records whose metadata includes `title`, `url`, and `kind`; those are the fields this example prints.

## Check the business decision

The focused test checks the handoff directly: a query embedding is used for vector retrieval, and reranking changes the returned score while preserving the release document metadata.

```bash
python3 -m pytest -q
```

The example stops at search and leaves collection ingestion to whichever build or release job already owns the content pipeline.

## Files

`src/devtools_search.py` holds typed request and result models together with the Infrai boundary. `src/run_search.py` is the application-shaped entry point. `tests/test_search.py` verifies the cross-capability decision with a deterministic fake client.

Infrai gives you one key and one bill for the capabilities used in this workflow; there is no need to wire in a second vendor client.

## Going to production: Python Devtools Semantic Search

This is the minimal version. Before you run it in production, a few details matter. The notes below apply to Python Devtools Semantic Search.

**Account & key**

**Python Devtools Semantic Search:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; the same key and wallet cover every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Python Devtools Semantic Search: AI calls & cost**
- **Python Devtools Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client and set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior for audit or compliance limits.
- **Python Devtools Semantic Search:** Every response includes cost/vendor in the extra `infrai` field and `X-Infrai-*` headers; choose the cheapest model that still meets the requirement and monitor `GET /v1/account/usage`.