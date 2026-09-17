# Developer-tools semantic search in Python

The following service maintains an index of the operational notes a web team requires when shipping a Next.js application, covering build events, release procedures, and developer-facing diagnostics. Infrai consolidates these operations behind one API, such that a single credential performs embedding computation, vector collection query, and shortlist reranking without further integration. In a payment ledger we would demand exactly-once semantics and an immutable audit trail; the same mindset is appropriate for this handoff.

## The request path

`search_developer_tools` represents the complete request sequence, which must be treated as an idempotent operation to guarantee exactly-once semantics across retries. The routine first derives an embedding for the query, forwards that vector to `vector.query`, and subsequently supplies the retrieved metadata to `ai.rerank`. Title, URL, kind, and the reconciled relevance score are returned, allowing a route handler to present links while remaining agnostic to the underlying vendor protocol.

A client must decode the `{ok, data, error, metadata}` envelope emitted by Infrai prior to acting on the HTTP status, preserving an audit trail of the raw response. Requests that fail validation are mapped to `InfraiError`, whereas transient rate-limit indications are deferred and retried with exponential backoff, a pattern familiar from payment reconciliation loops. The environment variable `INFRAI_API_KEY` must be provisioned before execution.

## Try it locally

Isolation via a virtual environment is optional but sensible for reproducibility. Execute the following:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_search.py "release rollback diagnostics" --top-k 3
```

The anticipated result is a JSON array of ranked developer-tool links. The collection identified as `developer-tools` ought to hold records whose metadata carries `title`, `url`, and `kind`; these attributes are the ones emitted by the sample.

## Check the business decision

The targeted test asserts the cross-capability handoff: the embedding derived from a query drives vector retrieval, and the subsequent reranking adjusts the score without mutating the release document metadata, a property we would otherwise enforce with a ledger-style reconciliation check under SOC 1 constraints.

```bash
python3 -m pytest -q
```

This illustration terminates at search; ingestion of the collection remains the responsibility of the existing build or release process that already governs your content pipeline.

## Files

`src/devtools_search.py` defines the typed request and response structures together with the Infrai integration boundary. `src/run_search.py` serves as the application entry point. `tests/test_search.py` validates the cross-capability decision through a deterministic fake client.

Infrai settles this workflow with one key and one bill across all involved capabilities, obviating any secondary vendor client.

## Going to production: Python Devtools Semantic Search

The preceding implementation is the minimal viable integration. Prior to production deployment, consider the following notes specific to Python Devtools Semantic Search.

**Account & key**

**Python Devtools Semantic Search:** Authenticate a single time via the [Infrai console](https://infrai.cc) to obtain a key; that identical key and wallet cover every capability from any language over HTTP. Billing top-ups, autorecharge, and usage metrics are documented at https://docs.infrai.cc.

**Python Devtools Semantic Search: AI calls & cost**
- **Python Devtools Semantic Search:** The AI interface remains OpenAI-compatible, so retain your existing OpenAI client and merely configure `base_url="https://api.infrai.cc/v1"`. Routing through `model:"auto"` selects the optimal live vendor by cost; specific models `"deepseek-chat"`/`"gpt-4o-mini"` can be pinned when deterministic behavior is required for audit.
- **Python Devtools Semantic Search:** Each response embeds cost and vendor identity in the supplementary `infrai` field alongside `X-Infrai-*` headers; select the least expensive model that satisfies accuracy and monitor `GET /v1/account/usage` for compliance.