#!/usr/bin/env python3
"""Idempotent batch import of graph.json into Neo4j."""
import json, os
from pathlib import Path
from neo4j import GraphDatabase

ROOT=Path(__file__).resolve().parents[1]
GRAPH=json.loads((ROOT/"data/graph.json").read_text())
URI=os.environ.get("NEO4J_URI","bolt://localhost:7687")
USER=os.environ.get("NEO4J_USERNAME","neo4j")
PASSWORD=os.environ.get("NEO4J_PASSWORD")
DATABASE=os.environ.get("NEO4J_DATABASE","neo4j")
BATCH=int(os.environ.get("NEO4J_BATCH_SIZE","500"))

if not PASSWORD:
    raise SystemExit("Set NEO4J_PASSWORD")

driver=GraphDatabase.driver(URI,auth=(USER,PASSWORD))
driver.verify_connectivity()

SCHEMA=[
"CREATE CONSTRAINT source_id IF NOT EXISTS FOR (n:SourceDocument) REQUIRE n.id IS UNIQUE",
"CREATE CONSTRAINT domain_id IF NOT EXISTS FOR (n:SkillDomain) REQUIRE n.id IS UNIQUE",
"CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (n:Skill) REQUIRE n.id IS UNIQUE",
"CREATE CONSTRAINT family_id IF NOT EXISTS FOR (n:JobFamily) REQUIRE n.id IS UNIQUE",
"CREATE CONSTRAINT role_id IF NOT EXISTS FOR (n:JobRole) REQUIRE n.id IS UNIQUE",
"CREATE CONSTRAINT portfolio_role_id IF NOT EXISTS FOR (n:PortfolioRole) REQUIRE n.id IS UNIQUE",
"CREATE CONSTRAINT person_id IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
]

def batches(rows):
    for i in range(0,len(rows),BATCH):
        yield rows[i:i+BATCH]

def run(q, rows):
    for batch in batches(rows):
        driver.execute_query(q, rows=batch, database_=DATABASE)

with driver:
    for q in SCHEMA:
        driver.execute_query(q,database_=DATABASE)

    driver.execute_query("""
    UNWIND $rows AS r
    MERGE (s:SourceDocument {id:r.id}) SET s.name=r.name, s.kind=r.kind
    """, rows=[
        {"id":"source:ats","name":"Blairs_Job_Titles_ATS.html","kind":"ATS role corpus"},
        {"id":"source:portfolio","name":"index.html","kind":"portfolio/resume source"}
    ], database_=DATABASE)

    driver.execute_query("""
    MERGE (p:Person {id:"person:blair-page"})
    SET p.name="Blair Page"
    """,database_=DATABASE)

    run("""
    UNWIND $rows AS r
    MERGE (d:SkillDomain {id:"domain:"+r.domain})
    SET d.name=r.domain
    """, GRAPH["skills"])

    run("""
    UNWIND $rows AS r
    MERGE (s:Skill {id:r.id})
    SET s.name=r.name, s.mention_count=r.mention_count, s.evidence=r.evidence
    WITH s,r
    MATCH (d:SkillDomain {id:"domain:"+r.domain})
    MERGE (s)-[:IN_DOMAIN]->(d)
    """, GRAPH["skills"])

    run("""
    UNWIND $rows AS r
    MERGE (rnode:JobRole {id:r.id})
    SET rnode.title=r.title, rnode.ats_potential=r.ats_potential,
        rnode.demand_signal=r.demand_signal, rnode.coverage_signal=r.coverage_signal,
        rnode.match=r.match, rnode.gap=r.gap, rnode.description=r.description
    WITH rnode,r
    MERGE (f:JobFamily {id:"family:"+r.family}) SET f.name=r.family
    MERGE (rnode)-[:IN_FAMILY]->(f)
    MATCH (src:SourceDocument {id:"source:ats"})
    MERGE (rnode)-[:SOURCED_FROM]->(src)
    """, GRAPH["ats_roles"])

    run("""
    UNWIND $rows AS r
    MATCH (rnode:JobRole {id:r.role_id})
    MATCH (s:Skill {id:r.skill_id})
    MERGE (rnode)-[rel:REQUIRES_SKILL]->(s)
    SET rel.weight=r.weight, rel.evidence=r.evidence
    """, GRAPH["role_skill_edges"])

    run("""
    UNWIND $rows AS r
    MERGE (p:PortfolioRole {id:r.id})
    SET p.title=r.title, p.context=r.context
    WITH p,r
    MATCH (src:SourceDocument {id:"source:portfolio"})
    MERGE (p)-[:SOURCED_FROM]->(src)
    """, GRAPH["portfolio_roles"])

    run("""
    UNWIND $rows AS r
    MATCH (p:PortfolioRole {id:r.role_id})
    MATCH (s:Skill {id:r.skill_id})
    MERGE (p)-[rel:USES_SKILL]->(s)
    SET rel.weight=r.weight, rel.evidence=r.evidence
    """, GRAPH["portfolio_skill_edges"])

    run("""
    UNWIND $rows AS r
    MATCH (s:Skill {id:r.skill_id})
    MATCH (src:SourceDocument {id:"source:portfolio"})
    MERGE (s)-[:SOURCED_FROM]->(src)
    """, GRAPH["skills"])

    run("""
    UNWIND $rows AS r
    MATCH (s1:Skill {name:r.from})
    MATCH (s2:Skill {name:r.to})
    MERGE (s1)-[rel:ENABLES]->(s2)
    SET rel.basis=r.basis
    """, GRAPH["skill_tree_edges"])

    driver.execute_query("""
    MATCH (p:Person {id:"person:blair-page"})
    MATCH (s:Skill)
    MERGE (p)-[:HAS_SKILL]->(s)
    """,database_=DATABASE)

print("Neo4j import complete.")
