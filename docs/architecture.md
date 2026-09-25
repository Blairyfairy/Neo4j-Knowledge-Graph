# Architecture

## Recommended production topology

```text
                         ┌──────────────────────┐
                         │ GitHub repository     │
                         │ parser + graph model  │
                         └──────────┬───────────┘
                                    │ CI/CD
                         ┌──────────▼───────────┐
                         │ Terraform             │
                         │ AWS IAM + S3 + runner  │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │ AWS ingestion runner   │
                         │ Python + Neo4j driver  │
                         └──────────┬───────────┘
                                    │ Bolt/TLS
                         ┌──────────▼───────────┐
                         │ Neo4j AuraDB on AWS    │
                         │ source-of-truth graph  │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │ GDS / dashboards / API │
                         └────────────────────────┘
```

### Design principles

- Keep the graph database managed rather than placing Neo4j itself on a general-purpose EC2 host.
- Use stable IDs and idempotent `MERGE` imports.
- Preserve source provenance.
- Separate source evidence from inferred graph logic.
- Treat ATS percentages as source-derived potential estimates.
- Use graph algorithms after deterministic ingestion, not as a substitute for normalization.
- Keep secrets outside Git.

### Why not a flat skill list?

A flat list cannot answer:

- Which job families share a skill?
- Which skills bridge Linux, cloud, databases and e-commerce?
- Which portfolio experiences provide evidence for a requested role?
- Which skills are foundational versus downstream?
- Which skills have high cross-role centrality?

The graph model answers these with traversals and graph analytics.
