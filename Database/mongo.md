
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