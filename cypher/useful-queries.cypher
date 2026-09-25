// Roles connected to a skill
MATCH (r:JobRole)-[:REQUIRES_SKILL]->(s:Skill {name:"AWS"})
RETURN r.title, r.family, r.ats_potential, r.demand_signal, r.coverage_signal
ORDER BY r.ats_potential DESC;

// Cross-source skill overlap
MATCH (p:PortfolioRole)-[:USES_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(r:JobRole)
RETURN s.name, count(DISTINCT p) AS portfolio_roles, count(DISTINCT r) AS ats_roles
ORDER BY ats_roles DESC;

// Skill tree
MATCH (s:Skill)-[:ENABLES]->(child:Skill)
RETURN s.name AS parent, child.name AS child
ORDER BY parent, child;

// Roles with broad skill coverage
MATCH (r:JobRole)-[:REQUIRES_SKILL]->(s:Skill)
WITH r, count(DISTINCT s) AS skill_count
RETURN r.title, r.family, r.ats_potential, skill_count
ORDER BY skill_count DESC, r.ats_potential DESC
LIMIT 50;

// Explain one role's evidence path
MATCH p=(r:JobRole {title:"Enterprise L3 Support Engineer"})-[:REQUIRES_SKILL]->(s:Skill)-[:SOURCED_FROM]->(src:SourceDocument)
RETURN p;

// Skills shared by a person and an ATS role
MATCH (p:Person {id:"person:blair-page"})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(r:JobRole)
RETURN s.name, count(DISTINCT r) AS role_count
ORDER BY role_count DESC;
