from neo4j import GraphDatabase

# Connect to local Neo4j instance
URI = "neo4j+s://54735458.databases.neo4j.io"
AUTH = ("neo4j", "xubGBJZ3Kigpr_8keBHM-v2WwwvjLzeJntB-XQBFpSY")  # replace with your actual password

driver = GraphDatabase.driver(URI, auth=AUTH)

print("Connected to Neo4j!")

def setup_world(tx):
    # Wipe old data
    tx.run("MATCH (n) DETACH DELETE n")

    # Create cities
    tx.run("""
    UNWIND range(1,5) AS id
    CREATE (:City {name: "City" + id});
    """)

    # Create linear roads
    tx.run("""
    MATCH (c1:City), (c2:City)
    WHERE c2.name = "City" + (toInteger(substring(c1.name,4)) + 1)
    MERGE (c1)-[:ROAD {distance: toInteger(rand()*10)+1}]->(c2)
    """)
    
with driver.session() as session:
    session.execute_write(setup_world)

def add_facilities(tx):
    # Create resource types
    tx.run("""
    MERGE (:Resource {name:"Wood"})
    MERGE (:Resource {name:"Food"})
    MERGE (:Resource {name:"Iron"})
    """)

    # City1 produces wood
    tx.run("""
    MATCH (c:City {name:"City1"}), (r:Resource {name:"Wood"})
    MERGE (f:Facility {id:"F1", type:"Lumber Mill", rate:10})
    MERGE (c)-[:HAS_FACILITY]->(f)
    MERGE (f)-[:PRODUCES {rate:10}]->(r)
    """)

    # City2 produces food + iron
    tx.run("""
    MATCH (c:City {name:"City2"}), (r1:Resource {name:"Food"}), (r2:Resource {name:"Iron"})
    MERGE (f:Facility {id:"F2", type:"Farm", rate:8})
    MERGE (c)-[:HAS_FACILITY]->(f)
    MERGE (f)-[:PRODUCES {rate:8}]->(r1)

    MERGE (f2:Facility {id:"F3", type:"Mine", rate:6})
    MERGE (c)-[:HAS_FACILITY]->(f2)
    MERGE (f2)-[:PRODUCES {rate:6}]->(r2)
    """)

    # City5 consumes wood
    tx.run("""
    MATCH (c:City {name:"City5"}), (r:Resource {name:"Wood"})
    MERGE (f:Facility {id:"F4", type:"Carpenter", rate:5})
    MERGE (c)-[:HAS_FACILITY]->(f)
    MERGE (f)-[:CONSUMES {rate:5}]->(r)
    """)

with driver.session() as session:
    session.execute_write(add_facilities)

def propagate_resources(tx, turn):
    # Step 1: Create initial JSON data for local consumption
    query_info = """
    MATCH (c:City)
    OPTIONAL MATCH (c)-[:HAS_FACILITY]->()-[rel:PRODUCES|CONSUMES]->(r:Resource)
    WITH c, r, rel,
         [x IN collect({type:type(rel), resource:r.name, rate:rel.rate, price:r.price})
          WHERE x.type='PRODUCES'] AS prod,
         [x IN collect({type:type(rel), resource:r.name, rate:rel.rate, price:r.price})
          WHERE x.type='CONSUMES'] AS cons
    WHERE size(prod) > 0 OR size(cons) > 0
    
    // Create / match ResourceInfo node without city property
    MERGE (c)-[:HAS_INFO]->(info:ResourceInfo {name: 'Resource Info - ' + c.name})
    SET info.consumption_data = apoc.convert.toJson(
        apoc.map.fromPairs(
            [cns IN cons |
                [ cns.resource,
                  apoc.map.fromPairs([
                      [ c.name,
                        {
                          rate: cns.rate,
                          price: cns.price,
                          origin_city: c.name,
                          origin_turn: $turn
                        }
                      ]
                  ])
                ]
            ]
        )
    )
    """
    tx.run(query_info, turn=turn)

    # Step 2: Move requests from one city to next, merging in query
    query_move = """
    // 1. Find origin city info and neighbor cities
    MATCH (c:City)-[:HAS_INFO]->(info:ResourceInfo {turn:$turn})
    MATCH (c)-[:ROAD]->(n:City)
    WHERE info.consumption_data IS NOT NULL
    
    // 2. Parse the JSON into a Cypher map
    WITH c, n, apoc.convert.fromJsonMap(info.consumption_data) AS dataMap
    
    // 3. Flatten to resource/source city rows
    UNWIND keys(dataMap) AS res
    UNWIND keys(dataMap[res]) AS srcCity
    WITH c, n, res, srcCity,
         dataMap[res][srcCity].rate AS rate,
         dataMap[res][srcCity].hops AS hops
    WHERE srcCity <> n.name
    
    // 4. Ensure neighbor has a ResourceInfo node for this turn
    MERGE (n)-[:HAS_INFO]->(ninfo:ResourceInfo {turn:$turn, name: 'Resource Info - City ' + coalesce(toString(n.number), n.name)})
    ON CREATE SET ninfo.consumption_data = apoc.convert.toJson({})
    
    // 5. Get existing JSON for neighbor (as a map) or empty
    WITH ninfo, res, srcCity, rate, hops,
         CASE
           WHEN ninfo.consumption_data IS NOT NULL
           THEN apoc.convert.fromJsonMap(ninfo.consumption_data)
           ELSE {}
         END AS existingMap
    
    // 6. Aggregate all new srcCity entries for each resource
    WITH ninfo, existingMap, res,
         collect([srcCity, {rate: rate, hops: hops + 1}]) AS pairsPerRes
    
    // 7. Build updated resource entries
    WITH ninfo, existingMap,
         collect([
           res,
           apoc.map.merge(
             coalesce(existingMap[res], {}),
             apoc.map.fromPairs(pairsPerRes)
           )
         ]) AS resEntries
    
    // 8. Keep untouched resources too
    WITH ninfo, existingMap, resEntries,
         [x IN resEntries | x[0]] AS updatedResKeys
    WITH ninfo,
         apoc.map.fromPairs(
           resEntries +
           [k IN keys(existingMap) WHERE NOT k IN updatedResKeys | [k, existingMap[k]]]
         ) AS mergedMap
    

    // 9. Debug output
    RETURN n.name AS neighbor, mergedMap
    """
    
    with driver.session() as session:
        results = session.run(query_move, turn=turn)
        print("=== MERGED MAP PER NEIGHBOR ===")
        for record in results:
            print(f"Neighbor: {record['neighbor']}")
            for k, v in record['mergedMap'].items():
                print(f"  Resource: {k} -> {v}")
        print("===============================")
    
    # tx.run(query_move, turn=turn)

      # // 9. Save back as JSON
      # SET ninfo.consumption_data = apoc.convert.toJson(mergedMap)

    # Step 3: Clean up duplicates / remove self-origin info
    query_merge = """
    MATCH (info:ResourceInfo {turn:$turn})
    WITH info,
         CASE
           WHEN info.consumption_data IS NOT NULL
           THEN apoc.convert.fromJsonMap(info.consumption_data)
           ELSE {}
         END AS dataMap
    WITH info,
         apoc.map.fromPairs(
           [res IN keys(dataMap) |
             [res,
              apoc.map.fromPairs(
                [srcCity IN keys(dataMap[res])
                 WHERE srcCity <> info.city |
                 [srcCity, dataMap[res][srcCity]]
                ]
              )
             ]
           ]
         ) AS cleanedMap
    SET info.consumption_data = apoc.convert.toJson(cleanedMap)
    """
    tx.run(query_merge, turn=turn)

   

# Run simulation loop
with driver.session() as session:
    for turn in range(1, 3):
        session.write_transaction(propagate_resources, turn)
        print(f"Turn {turn} complete")