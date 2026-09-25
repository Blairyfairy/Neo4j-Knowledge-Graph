// Run after the graph is imported.
// GDS is optional; these queries are for analytical extension.

// Project role/skill bipartite graph.
// Relationship orientation: JobRole -> Skill.
CALL gds.graph.project(
  'roleSkill',
  ['JobRole','Skill'],
  {REQUIRES_SKILL:{orientation:'UNDIRECTED'}}
);

// Identify central skills that connect many role families.
CALL gds.degree.stream('roleSkill')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS n, score
WHERE n:Skill
RETURN n.name AS skill, score
ORDER BY score DESC
LIMIT 30;

// Cleanup when finished.
// CALL gds.graph.drop('roleSkill');
