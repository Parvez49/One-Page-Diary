# Elasticsearch

> Other datastores: **[nosql.md](nosql.md)** · Postgres full-text alternative:
> **[postgres.md](postgres.md)**

---

## 1. What it is, and when you need it ⭐

A **distributed search and analytics engine built on Apache Lucene**. Stores JSON documents and
provides near-real-time full-text search, filtering, aggregations, and log analytics.

⭐⭐ **The question that matters: why not just use `LIKE '%term%'` or Postgres full-text?**

| Need | Answer |
|---|---|
| Exact/prefix matching, modest scale | ⭐ **Postgres** — `LIKE 'abc%'`, `tsvector` + GIN |
| ⭐ **Relevance ranking**, typo tolerance, stemming, synonyms | ⭐⭐ **Elasticsearch** |
| Faceted search + aggregations over millions of docs | Elasticsearch |
| Log/metric analytics at scale | Elasticsearch (ELK) |
| Source of truth / transactions | ⚠️ **never** Elasticsearch |

⭐ **The dividing line is *relevance*.** SQL answers "does this row match?" — a boolean.
Elasticsearch answers "**how well** does this document match, relative to the others?" and sorts
by that score. Fuzzy matching, stemming ("running" → "run"), synonyms, and multi-field boosting
are the reason it exists.

⚠️⚠️ **Elasticsearch is not a database of record.** No ACID transactions, no joins, no
referential integrity, and it's near-real-time (a document isn't searchable until refresh).
Keep the truth in Postgres and **index into Elasticsearch as a derived, rebuildable store**
([nosql.md §7](nosql.md)).

---

## 2. Architecture ⭐

```
CLUSTER  ─┬─ NODE (master-eligible / data / ingest / coordinating)
          │
          └─ INDEX ─┬─ SHARD (primary)   ← ⭐ each shard IS a Lucene index
                    ├─ SHARD (replica)   ← ⭐ redundancy AND read throughput
                    └─ each shard = many immutable SEGMENTS
```

| Concept | Meaning |
|---|---|
| **Cluster** | nodes sharing a cluster name; one elected **master** handles cluster state |
| **Node** | a single instance; roles: master-eligible, data, ingest, coordinating |
| **Index** | a collection of similar documents (⭐ roughly "a table") |
| **Shard** | ⭐ a self-contained Lucene index — the **unit of scaling and distribution** |
| **Replica** | a copy of a shard on another node — ⭐ failover **and** parallel reads |
| **Segment** | ⭐ **immutable** Lucene file; new docs go to a buffer, then flush to a segment |
| **Document** | a JSON object |
| **Mapping** | ⭐ the schema: field types, indexing behaviour, analysers |

⭐⭐ **Segments are immutable — that explains most of Elasticsearch's behaviour:**

- **Updates are delete + reinsert**; the old version is only *marked* deleted.
- **Deletes don't free space** until segments are **merged** in the background.
- ⚠️ **Heavy update workloads cause segment churn and merge pressure** — Elasticsearch suits
  append-mostly data far better than frequently-mutated records.
- Immutability is also why reads need no locks and why segment files cache so well.

⚠️⚠️ **Shard count is fixed at index creation** and cannot be changed — you must reindex or use
the split/shrink APIs. **Over-sharding is the most common operational mistake**: each shard
carries fixed overhead (memory, file handles, cluster state), so thousands of tiny shards
degrade the whole cluster. ⭐ Aim for shards of roughly **10–50 GB**.

---

## 3. The inverted index ⭐⭐

**The core data structure, and the reason full-text search is fast.**

```
Documents:                     Inverted index:
1: "the quick brown fox"       brown → [1, 2]
2: "the brown dog"             dog   → [2]
3: "quick fox jumps"           fox   → [1, 3]
                               quick → [1, 3]
```

⭐ Instead of scanning every document for a term, look the **term** up and get the document list
immediately — the same idea as a book's index. That's O(1)-ish per term, versus a full scan.

**Analysis — how text becomes terms:**

```
"The Quick Brown Foxes!"
   ↓ character filters      strip HTML, replace characters
   ↓ tokenizer              ["The", "Quick", "Brown", "Foxes"]
   ↓ token filters          lowercase → stop words → ⭐ stemming
   → ["quick", "brown", "fox"]
```

⭐⭐ **The same analyser must run at index time and query time** — that's what makes searching
"foxes" find "fox". ⚠️ **Mismatched analysers are the classic "why does my search return
nothing?" bug**: the document was indexed as `fox` but the query searched for `Foxes`.

**`text` vs `keyword` — the mapping decision people get wrong:**

| | **`text`** | **`keyword`** |
|---|---|---|
| Analysed | ⭐ yes — tokenised, stemmed | ❌ no — stored whole |
| Use for | ⭐ full-text search (titles, body) | ⭐ **exact match, filters, aggregations, sorting** |
| `WHERE status = 'active'` | ⚠️ unreliable | ⭐ correct |

⭐ **Multi-fields let you have both:** `title` as `text` for search and `title.keyword` for
sorting/faceting. ⚠️ Sorting or aggregating on a `text` field either fails or gives nonsense
(it aggregates *tokens*, not values).

---

## 4. Querying ⭐

```json
GET /products/_search
{
  "query": {
    "bool": {
      "must":   [{ "match": { "name": "wireless headphone" }}],   // ⭐ SCORED
      "filter": [{ "term":  { "category": "audio" }},             // ⭐⭐ not scored → CACHED
                 { "range": { "price": { "lte": 200 }}}],
      "should": [{ "match": { "brand": "sony" }}],                // boosts score
      "must_not":[{ "term": { "discontinued": true }}]
    }
  },
  "aggs": { "by_brand": { "terms": { "field": "brand.keyword" }}}  // ⭐ facets
}
```

⭐⭐ **`filter` vs `must` is the highest-value performance distinction.** `must` computes a
relevance score; **`filter` is a yes/no test that is not scored and *is* cached**. Put every
exact/range condition in `filter` — it's faster and the filter bitset is reused across queries.

| Query | Use |
|---|---|
| `match` | ⭐ analysed full-text |
| `match_phrase` | words in order |
| `multi_match` | ⭐ search several fields, with boosting (`title^3`) |
| `term` | ⚠️ **exact, not analysed** — use on `keyword` fields only |
| `terms` / `range` / `exists` | filters |
| `fuzzy` / `match` with `fuzziness` | ⭐ typo tolerance (edit distance) |
| `bool` | combine the above |

⚠️ **`term` on a `text` field usually returns nothing** — the field was analysed into lowercase
tokens, so `term: "Sony"` never matches the stored `sony`. The other classic mapping bug.

**Relevance scoring:** **BM25** (the default) — term frequency, inverse document frequency, and
field-length normalisation. ⭐ Tune with field boosting and `function_score` (recency,
popularity) rather than fighting the algorithm.

⚠️ **Deep pagination is expensive** — `from: 10000` makes every shard produce and discard those
results. Use **`search_after`** (keyset-style) or the scroll/PIT API for exports — the same
problem and fix as SQL `OFFSET` ([performance.md](performance.md)).

---

## 5. Indexing & operations ⭐

```
POST /_bulk                      ⭐ ALWAYS bulk — one doc per request wastes the cluster
{"index": {"_index": "products", "_id": "1"}}
{"name": "Headphones", "price": 199}
```

⭐ **Near-real-time:** a document isn't searchable until the next **refresh** (default 1 s).
Raising `refresh_interval` (or setting `-1` during a bulk load) dramatically improves indexing
throughput. ⚠️ `?refresh=true` on every write destroys performance — it forces a segment flush.

**Durability:** a **translog** (write-ahead log) makes writes durable before segments are
flushed — the same idea as a database WAL ([transactions.md](transactions.md)).

⭐ **Reindexing is a normal operation, not a failure.** Mappings are mostly immutable — you
cannot change a field's type in place. The standard pattern:

```
create new index with the corrected mapping → _reindex → swap an ALIAS → drop the old index
```

⭐ **Always query through an alias**, never a concrete index name — it makes zero-downtime
reindexing possible.

**Time-series data (logs/metrics):** use **data streams** with **ILM** (index lifecycle
management) — hot → warm → cold → delete. ⭐ Dropping an old index is instant, exactly like
partition pruning in SQL ([scaling.md](scaling.md)).

⚠️ **Heap:** set the JVM heap to **≤ 50% of RAM and under ~31 GB** (above that the JVM loses
compressed object pointers). The rest of RAM serves the OS file cache, which is what actually
makes Lucene fast.

⚠️ **Cluster health:** `green` = all shards allocated · `yellow` = replicas unassigned (common
on a single node) · `red` = ⚠️ a **primary** shard missing, meaning data is unavailable.

---

## 6. Keeping it in sync ⭐

```
Postgres (source of truth)  ──▶  outbox / CDC (Debezium)  ──▶  Elasticsearch
```

⚠️⚠️ **Dual writes are the standard mistake** — writing to Postgres and Elasticsearch from
application code means one succeeds and the other fails, silently and permanently. Use the
**outbox pattern** or CDC so indexing derives from committed database state
([transactions.md §8](transactions.md)).

⭐ **Design for full reindex.** The index must be rebuildable from the source of truth at any
time — that's your recovery mechanism for mapping changes, bugs, and drift.

---

## 7. Interview points

- **What is Elasticsearch, and when do you need it? ⭐⭐** A distributed search engine over
  Lucene — use it when you need **relevance ranking**, stemming, typo tolerance, or faceted
  aggregations at scale. Not for exact lookups Postgres handles fine.
- **Why not just `LIKE '%term%'`?** No index can serve a leading wildcard, and it gives no
  ranking, stemming, or fuzziness.
- **Explain the inverted index. ⭐** Term → list of documents containing it, so lookup is by term
  rather than by scanning documents.
- **What is analysis, and why does search sometimes return nothing? ⭐⭐** Text is tokenised,
  lowercased, and stemmed at both index and query time — **mismatched analysers** (or `term` on
  a `text` field) mean the query never matches the stored tokens.
- **`text` vs `keyword`? ⭐⭐** Analysed for full-text vs stored whole for exact matching,
  filtering, sorting, and aggregations. Use multi-fields to get both.
- **`filter` vs `must` in a bool query? ⭐⭐** `filter` is unscored and **cached** — put every
  exact/range condition there.
- **What is a shard, and what's the common mistake? ⭐** A self-contained Lucene index and the
  unit of distribution; **over-sharding** — thousands of small shards — degrades the cluster.
  Target 10–50 GB per shard.
- **Can you change the shard count?** No — reindex, or use the split/shrink APIs.
- **Why are segments immutable, and what follows? ⭐** Lock-free reads and good caching — but
  updates are delete+reinsert, deletes free space only on merge, and heavy updates cause merge
  pressure.
- **What does "near-real-time" mean?** Documents become searchable at the next refresh (~1 s),
  not on write.
- **How do you change a mapping in production? ⭐** You can't in place — create a new index,
  `_reindex`, and swap an **alias**.
- **How do you keep Elasticsearch in sync with Postgres? ⭐⭐** Outbox or CDC from the source of
  truth — never dual writes — and keep a full reindex possible.
- **What does a red cluster mean?** A primary shard is unassigned — that data is unavailable.
