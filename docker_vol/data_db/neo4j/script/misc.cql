MATCH (n:Occupation)
WHERE n.preferredLabel CONTAINS 'computer scien'
RETURN n;

// Essential skills for a certain occupation
MATCH (n:Occupation)-[rel]-(c:Skill)
WHERE rel.type = 'essential'
AND n.preferredLabel CONTAINS 'data'
RETURN c, n

// Skill contains preferredLabel, altLabels and hiddenLabels for skill identification, description could be used too
MATCH (n:Skill)
WHERE n.preferredLabel CONTAINS 'SQL'
RETURN n;

MATCH (n:Skillgroup)
WHERE n.preferredLabel CONTAINS 'data'
MATCH (c)-[relation]-(n)
RETURN c, n


// Essential skills for a certain occupation - Skill = SQL
MATCH (n:Occupation)-[rel]-(c:Skill)
WHERE c.preferredLabel CONTAINS 'SQL'
RETURN c.preferredLabel, n.preferredLabel
