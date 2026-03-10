# Elasticsearch
- is a distributed search & analytics engine build on top of Apache lucene.
- It stores data as JSON documents and provides near real-time full-text search, filtering, aggregations, log analytics, autocomplete, recommendation/search systems and analytics.

## Key Components
- cluster:
  - is a collection of nodes that together store and search data.
  - all nodes identified by a unique cluster name.
  - One node is elected as the master node responsible for cluster-wide operations (index creation/deletion, shard allocation, node tracking).
- Index
  - is a collection of documents that share similar characteristics.
- Shard
  - is an Apache Lucene index. Each shard is a self-contained search engine. Shards are distributed across nodes.
- Segment
  - Immutable Lucene segments within a shard.
  - New documents are written to an in-memory buffer, then flushed to segments.
  - Segments are periodically merged to reduce count and reclaim space from deleted docs.
- Document
  - is a JSON object stored inside an index.
- Mapping
  - defines how documents and fields are stored and indexed in elasticsearch.
  - It is similar to sql schema.
    ```
      {
        "properties": {
          "name": { "type": "text" },
          "price": { "type": "float" },
          "category": { "type": "keyword" }
        }
      }
    ```
  - Mapping controls: field type, indexing behavior, analyzers.
