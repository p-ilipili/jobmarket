// Create the database (if it doesn't exist)
//CREATE DATABASE neo4j_jmdb;

// Switch to the newly created database
//:use neo4j_jmdb

//Import ESCO using CSV files
create index ON :Occupation(ISCOGroup);
create index ON :Occupation(altLabels);
create index ON :Skill(altLabels);
create index ON :ISCOGroup(code);
create index ON :Skill(conceptUri);
create index ON :ISCOGroup(conceptUri);
create index ON :Occupation(conceptUri);
create index ON :Occupation(preferredLabel);
create index ON :Skill(preferredLabel);

//import skills and skillgroups
//skillgroups are also skills
load csv with headers from "file:///skillGroups_en.csv" as row
create (s:Skill:Skillgroup)
set s = row;
//skills
load csv with headers from "file:///skills_en.csv" as row
create (s:Skill)
set s = row;
//add the BROADER_THAN relationship between different skills
load csv with headers from "file:///broaderRelationsSkillPillar.csv" as row
match (smaller:Skill {conceptUri: row.conceptUri}), (broader:Skill {conceptUri: row.broaderUri})
create (broader)-[:BROADER_THAN]->(smaller);

//import occupations
load csv with headers from "file:///occupations_en.csv" as row
create (o:Occupation)
set o = row;

//import the International Standard Classification for Occupations of the ILO
load csv with headers from "file:///ISCOGroups_en.csv" as row
create (isco:ISCOGroup)
set isco = row;
//impirt the BROADER_THAN relationships between ISCO groups
load csv with headers from "file:///broaderRelationsOccPillar.csv" as row
match (smaller:ISCOGroup {conceptUri: row.conceptUri}), (broader:ISCOGroup {conceptUri: row.broaderUri})
create (broader)-[:BROADER_THAN]->(smaller);
//connect the occupations to their ISCOGroup
match (isco:ISCOGroup), (o:Occupation)
where isco.code = o.iscoGroup
create (o)-[:PART_OF_ISCOGROUP]->(isco);

//Connect Skills to Occupations
using periodic commit 500
load csv with headers from "file:///occupationSkillRelations.csv" as row
match (s:Skill {conceptUri: row.skillUri}), (o:Occupation {conceptUri: row.occupationUri})
CREATE (s)-[:RELATED_TO {type: row.relationType}]->(o);

// match ()-[r:RELATED_TO]->()
// return distinct r.type;

//differentiate the different types of relations between occupations and skills
match (a)-[r:RELATED_TO]->(b)
where r.type = "essential"
create (a)-[:ESSENTIAL_FOR]->(b);
match (a)-[r:RELATED_TO]->(b)
where r.type = "optional"
create (a)-[:OPTIONAL_FOR]->(b);
//remove the old relationships
match (a)-[r:RELATED_TO]->(b)
delete r;
