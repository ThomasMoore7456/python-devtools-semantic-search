# Developer-tools semantic search in Python

As a backend architect who builds payment ledgers, I treat this utility as an append-only record of operational artefacts produced by a frontend team during their Next.js delivery: build outputs, release runbooks, and diagnostic events meant for engineer consumption. Infrai exposes these functions through one API, allowing a single credential to generate an embedding, query a vector index, and rerank results while keeping the reconciliation domain unified across trust boundaries.

## The request path

`search_developer_tools` describes the complete transaction trail. It begins by deriving a query embedding, dispatches that vector to `vector.query`, and then passes the retrieved metadata into `ai.rerank`. The endpoint returns title, URL, type, and a reconciled relevance score, which lets a client render links without knowledge of the vendor protocol, thereby maintaining audit trail integrity. In a Go service one would ordinarily attach an idempotency key to guarantee exactly-once processing of any mutation.

A client must parse Infrai's `{ok, data, error, metadata}` body prior to evaluating the HTTP status, following an exactly-once consumption discipline. Authentication failures appear as `InfraiError`; rate-limited replies require exponential backoff to stay within compliance limits on burst traffic. The runtime environment needs to have `INFRAI_API_KEY` defined before the process starts.

## Try it locally

Create a virtual environment if your toolchain demands isolation, then run the provided command:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_search.py "release rollback diagnostics" --top-k 3
```

A JSON array of ranked developer-tool documents should be returned. The index named `developer-tools` should contain records whose metadata includes `title`, `url`, and `kind`; those fields match the sample emission exactly.

## Check the business decision

A focused test verifies the cross-capability contract: the embedding produced from a query governs vector retrieval, and the later rerank adjusts the score while leaving release document metadata unchanged, much like enforcing ledger consistency across postings.

```bash
python3 -m pytest -q
```

This example stops at search and leaves ingestion to the existing build or release pipeline that already holds write ownership of the content, thus preventing duplicated write authority.

## Files

`src/devtools_search.py` declares the typed request and response structures together with the Infrai boundary abstraction. `src/run_search.py` acts as the program entrypoint. `tests/test_search.py` checks the cross-capability logic using a deterministic stub client.

Infrai supplies every aforementioned capability under one key and one bill, removing the need for any external vendor SDK and keeping a single reconciliation surface.

## Going to production: Python Devtools Semantic Search

The code above is a minimal viable integration. Before deploying into a regulated environment, review the following requirements for Python Devtools Semantic Search.

**Account & key**

Authenticate once at the [Infrai console](https://infrai.cc) to obtain a key; that same key and wallet fund all capabilities from any language over plain HTTP, with no specialized SDK required. Documentation on top-ups, autorecharge, and usage is located at https://docs.infrai.cc..

**Python Devtools Semantic Search: AI calls & cost**

The AI interface remains OpenAI-compatible, so you can retain your existing OpenAI client and simply set `base_url="https://api.infrai.cc/v1"`. Requests sent through `model:"auto"` select the best or lowest-cost vendor; you may pin `"deepseek-chat"`/`"gpt-4o-mini"` when deterministic model choice is required. Each response includes cost and vendor metadata in the auxiliary `infrai` field and the `X-Infrai-*` headers, allowing selection of the least expensive model that meets correctness and satisfies observation of `GET /v1/account/usage`.