# Blair Skill Knowledge Graph

An evidence-backed Neo4j knowledge graph that connects Blair Page's ATS role corpus to the technical, cloud, data, e-commerce, support, product, and business skills evidenced in the portfolio.

## Source material

- `Blairs_Job_Titles_ATS.html` — 327 ATS role records with role family, ATS potential, demand/coverage signals, match notes, and gaps.
- `index(6).html` — portfolio/resume source containing professional experience, technology vocabulary, certifications, education, projects, and business/product experience.

The ATS page itself describes its percentages as **tailored-resume ATS potential estimates**, not measured employer ATS results. The graph preserves that distinction as `ats_potential`.

## Portfolio links

- https://blairyfairy.github.io/portfolio-card/
- https://blairyfairy.github.io/BlairPage/

## Graph model

```text
(Person:Blair)
   └─[:HAS_SKILL]→ (Skill)
                         └─[:IN_DOMAIN]→ (SkillDomain)
                         └─[:ENABLES]→ (Skill)

(JobRole)
   ├─[:IN_FAMILY]→ (JobFamily)
   ├─[:REQUIRES_SKILL]→ (Skill)
   └─[:SOURCED_FROM]→ (SourceDocument)

(PortfolioRole)
   ├─[:USES_SKILL]→ (Skill)
   └─[:SOURCED_FROM]→ (SourceDocument)

(Skill)
   └─[:SOURCED_FROM]→ (SourceDocument)
```

### Why this model

The professional approach is **not** to create one giant `skills` text field. It separates:

1. **Canonical skills** — reusable nodes such as Linux, AWS, MySQL, Terraform, Ansible, Docker, Magento and L3 Support.
2. **Skill domains** — Cloud & Infrastructure, Linux & Systems, Databases & Data, DevOps & Automation, Web & E-commerce, Observability & Security, Enterprise & Support, Product & Business, Programming & Engineering, and Credentials & Education.
3. **Job roles** — the 327 ATS role records remain independently queryable.
4. **Evidence/source provenance** — every imported source family is retained.
5. **Inferred skill-tree logic** — `ENABLES` edges are explicitly marked `basis=design_inference`, so inferred relationships are not confused with source evidence.

## Import strategy

For this dataset, the recommended architecture is:

**HTML → deterministic parser → normalized JSON → Neo4j batch importer → Cypher/GDS analysis**

The importer uses parameterized Cypher and `UNWIND` batches rather than issuing one transaction per node/edge.

For production, the recommended target is **Neo4j AuraDB on AWS**, with AWS infrastructure managed by Terraform and the ingestion runner configured by Ansible. Aura is managed by Neo4j, avoiding the operational burden of running the database itself on an EC2 instance.

Neo4j provides a Terraform provider for Aura, but it is currently a Neo4j Labs project rather than an officially supported Neo4j offering; therefore this repository keeps Aura provisioning as an optional IaC layer and does not hide that dependency.

## Repository layout

```text
.
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
├── Makefile
├── data/
│   ├── graph.json
│   ├── skills.json
│   └── ats_roles.json
├── scripts/
│   ├── parse_sources.py
│   ├── import_neo4j.py
│   └── validate_graph.py
├── cypher/
│   ├── schema.cypher
│   ├── useful-queries.cypher
│   └── gds-analytics.cypher
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── aura-provider.example.tf
├── ansible/
│   ├── inventory.example.ini
│   ├── site.yml
│   └── templates/neo4j-importer.env.j2
└── docs/
    └── architecture.md
```

## Local Neo4j test

Requires Docker.

```bash
docker compose up -d
```

Then:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=change-me

python scripts/import_neo4j.py
python scripts/validate_graph.py
```

The local password is defined in `docker-compose.yml` for development only. Do not reuse it in AWS.

## Rebuild the graph from the HTML sources

Put the two source files in `sources/`:

```text
sources/Blairs_Job_Titles_ATS.html
sources/index.html
```

Then:

```bash
python scripts/parse_sources.py
```

The parser writes `data/graph.json`.

## AWS / Terraform / Ansible

The intended production flow is:

```text
GitHub
  │
  ├── Terraform
  │    ├── AWS S3 data/artifact bucket
  │    ├── IAM role/policy
  │    └── ingestion runner security boundary
  │
  ├── Neo4j AuraDB on AWS
  │
  └── Ansible
       ├── configure ingestion host
       ├── install Python/runtime
       ├── install project
       └── configure environment/secrets
                │
                ▼
         Python batch importer
                │
                ▼
             Neo4j
```

Keep Neo4j credentials out of Git. Use AWS Secrets Manager/SSM or another approved secret-management mechanism for production.

## Useful graph questions

Find roles connected to AWS and Terraform:

```cypher
MATCH (r:JobRole)-[:REQUIRES_SKILL]->(s:Skill)
WHERE s.name IN ['AWS', 'Terraform']
RETURN r.title, r.family, r.ats_potential, collect(s.name) AS skills
ORDER BY r.ats_potential DESC;
```

Find the skill tree below DevOps:

```cypher
MATCH (d:SkillDomain {name:'DevOps & Automation'})<-[:IN_DOMAIN]-(s:Skill)
OPTIONAL MATCH (s)-[:ENABLES]->(child:Skill)
RETURN s.name, collect(child.name) AS enables;
```

Find roles with the densest technical coverage:

```cypher
MATCH (r:JobRole)-[:REQUIRES_SKILL]->(s:Skill)
WITH r, count(DISTINCT s) AS skill_count
RETURN r.title, r.family, r.ats_potential, skill_count
ORDER BY skill_count DESC, r.ats_potential DESC
LIMIT 50;
```

Find skills shared by portfolio roles and ATS roles:

```cypher
MATCH (p:PortfolioRole)-[:USES_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(r:JobRole)
RETURN s.name,
       count(DISTINCT p) AS portfolio_roles,
       count(DISTINCT r) AS ats_roles
ORDER BY ats_roles DESC, portfolio_roles DESC;
```

## GDS extension

Once the graph is loaded, Neo4j Graph Data Science can be used for graph projections, centrality, community detection, similarity and machine-learning workflows. The repository includes starter Cypher in `cypher/gds-analytics.cypher`.

A useful next-stage analysis is to calculate skill centrality and identify **bridge skills** that connect multiple job families. That is more informative than simply counting keyword frequency.

## Data-quality rules

- Source-derived facts remain attached to their source document.
- ATS percentages are stored as `ats_potential`, not `ats_score`.
- Inferred `ENABLES` relationships are marked as inference.
- Skill names are canonicalized before import.
- Imports use stable IDs and `MERGE` to make reruns idempotent.
- Credentials and education are not treated as interchangeable with technical skills.
- Missing evidence is not silently invented.

## Official technical references

- Neo4j Aura: https://neo4j.com/docs/aura/
- Aura API: https://neo4j.com/docs/aura/api/overview/
- Neo4j Python Driver: https://neo4j.com/docs/python-manual/current/
- Neo4j GDS: https://neo4j.com/docs/graph-data-science/current/
- Neo4j Aura Terraform Provider: https://neo4j.com/labs/neo4j-aura-terraform-provider/

## GitHub

This directory is already initialized as a Git repository and contains the complete project. After creating the GitHub repository, push it with:

```bash
git remote add origin https://github.com/blairyfairy/blair-skill-knowledge-graph.git
git branch -M main
git add .
git commit -m "Build evidence-backed Blair skill knowledge graph"
git push -u origin main
```
