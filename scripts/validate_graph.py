#!/usr/bin/env python3
import json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
g=json.loads((ROOT/"data/graph.json").read_text())
assert len(g["ats_roles"]) == g["metadata"]["ats_role_count"]
assert len(g["skills"]) == g["metadata"]["skill_count"]
assert len({s["id"] for s in g["skills"]}) == len(g["skills"])
assert all(e["basis"]=="design_inference" for e in g["skill_tree_edges"])
print("Offline validation passed.")
print("ATS roles:",len(g["ats_roles"]))
print("Skills:",len(g["skills"]))
print("Portfolio roles:",len(g["portfolio_roles"]))
print("ATS role-skill edges:",len(g["role_skill_edges"]))
print("Portfolio role-skill edges:",len(g["portfolio_skill_edges"]))
print("Skill-tree edges:",len(g["skill_tree_edges"]))

if os.getenv("NEO4J_PASSWORD"):
    from neo4j import GraphDatabase
    driver=GraphDatabase.driver(os.getenv("NEO4J_URI","bolt://localhost:7687"),
                                auth=(os.getenv("NEO4J_USERNAME","neo4j"),os.environ["NEO4J_PASSWORD"]))
    with driver:
        for q in [
            "MATCH (n:JobRole) RETURN count(n) AS c",
            "MATCH (n:Skill) RETURN count(n) AS c",
            "MATCH ()-[r:REQUIRES_SKILL]->() RETURN count(r) AS c",
            "MATCH ()-[r:HAS_SKILL]->() RETURN count(r) AS c",
        ]:
            print(driver.execute_query(q,database_=os.getenv("NEO4J_DATABASE","neo4j")).records[0]["c"])
