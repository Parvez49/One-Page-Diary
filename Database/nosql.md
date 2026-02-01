### NoSQL 
- databases are non-relational databases., they do NOT require fixed tables or schemas.
- Often optimized for speed & horizontal scaling, best for Chat, Feed, Analytics.
- Relationships are usually handled in application code, not DB-level.
- Example:
  - MongoDB (Document): Data is stored as JSON-like documents
    ```
    {
      "_id": "123",
      "name": "Name",
      "user_id": 1,  // user_id looks like a foreign key but mongo doesn't have forign-key
      "orders": [
        { "id": 1, "amount": 500 },
        { "id": 2, "amount": 900 }
      ]
    }
    ```
  - Redis (Key-Value): Key-Value store: "user:123" → "{name: Parvez, age: 25}"
  - Cassandra (Wide-Column): Tables but dynamic columns
  - Neo4j (Graph): Nodes + edges, Perfect for social networks, (Graph)
  - DynamoDB
- SQL enforces relationships using foreign keys and ensures strong consistency, while NoSQL trades strict relations for scalability, flexibility, and performance, handling relationships at the application level.
- When MongoDB is a BAD choice?
  - when strong relationships, strict consistency(Order must always belong to a valid user), and complex joins are core business requirements.

### Elasticsearch
- is a distributed search & analytics engine.
- optimized for fast text search & aggregation
- 


## Export Docker Mongo Database
```commandline
docker exec -it pyjin_mongo_service mongodump \
  --username=<root> \
  --password=<password> \
  --authenticationDatabase=<admin> \
  --db=<DevTool> \
  --out=</data/backup>   // this is docker instance directory

```
### This command copy docker instance to local machine
```commandline
docker cp pyjin_mongo_service:/data/backup ./mongo_backup

```
### Import backup database to docker mongo database instance
####  Cope backup data to docker mongo container instance in backup directory
```commandline
docker cp mongo_backup pyjin_mongo_service:/data/backup
```
```commandline
docker exec -it pyjin_mongo_service mongorestore \
  --username=<root> \
  --password=<password> \
  --authenticationDatabase=<admin> \
  --db=<DevTool> \
  /data/backup/DevTool


```
