// Create the database (if it doesn't exist)
//CREATE DATABASE neo4j_jmdb;

// Switch to the newly created database
//:use neo4j_jmdb

//Import ESCO using CSV files
CREATE INDEX FOR (o:Occupation) ON (o.ISCOGroup);
CREATE INDEX FOR (o:Occupation) ON (o.altLabels);
CREATE INDEX FOR (s:Skill) ON (s.altLabels);
CREATE INDEX FOR (i:ISCOGroup) ON (i.code);
CREATE INDEX FOR (s:Skill) ON (s.conceptUri);
CREATE INDEX FOR (i:ISCOGroup) ON (i.conceptUri);
CREATE INDEX FOR (o:Occupation) ON (o.conceptUri);
CREATE INDEX FOR (o:Occupation) ON (o.preferredLabel);
CREATE INDEX FOR (s:Skill) ON (s.preferredLabel);

// Import skills and skill groups
// Skill groups are also skills
LOAD CSV WITH HEADERS FROM "file:///skillGroups_en.csv" AS row
CREATE (s:Skill:Skillgroup)
SET s = row;

// Skills
LOAD CSV WITH HEADERS FROM "file:///skills_en.csv" AS row
CREATE (s:Skill)
SET s = row;

// Add the BROADER_THAN relationship between different skills
LOAD CSV WITH HEADERS FROM "file:///broaderRelationsSkillPillar_en.csv" AS row
MATCH (smaller:Skill {conceptUri: row.conceptUri}), (broader:Skill {conceptUri: row.broaderUri})
CREATE (broader)-[:BROADER_THAN]->(smaller);

// Import occupations
LOAD CSV WITH HEADERS FROM "file:///occupations_en.csv" AS row
CREATE (o:Occupation)
SET o = row;

// Import the International Standard Classification for Occupations (ISCO) of the ILO
LOAD CSV WITH HEADERS FROM "file:///ISCOGroups_en.csv" AS row
CREATE (isco:ISCOGroup)
SET isco = row;

// Import the BROADER_THAN relationships between ISCO groups
LOAD CSV WITH HEADERS FROM "file:///broaderRelationsOccPillar_en.csv" AS row
MATCH (smaller:ISCOGroup {conceptUri: row.conceptUri}), (broader:ISCOGroup {conceptUri: row.broaderUri})
CREATE (broader)-[:BROADER_THAN]->(smaller);

// Connect the occupations to their ISCO group
MATCH (isco:ISCOGroup), (o:Occupation)
WHERE isco.code = o.iscoGroup
CREATE (o)-[:PART_OF_ISCOGROUP]->(isco);

// Connect skills to occupations
    LOAD CSV WITH HEADERS FROM "file:///occupationSkillRelations_en.csv" AS row
    MATCH (s:Skill {conceptUri: row.skillUri}), (o:Occupation {conceptUri: row.occupationUri})
    CREATE (s)-[:RELATED_TO {type: row.relationType}]->(o)
    RETURN null AS placeholder

// Differentiate the different types of relations between occupations and skills
MATCH (a)-[r:RELATED_TO]->(b)
WHERE r.type = "essential"
CREATE (a)-[:ESSENTIAL_FOR]->(b);

MATCH (a)-[r:RELATED_TO]->(b)
WHERE r.type = "optional"
CREATE (a)-[:OPTIONAL_FOR]->(b);

// Remove the old relationships
MATCH (a)-[r:RELATED_TO]->(b)
DELETE r;
