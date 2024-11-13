## Basic Command

```
sudo -i -u postgres // to activate psql databases.
psql  // to run psql command.

\l                   //list all databases
\c dbname            //connect to differnent databases.
\dt                  // list all tables of current databases
\d table_name        // to describe table.

SELECT version();

\q         // to exit from psql command prompt
exit       // to back terminal location.
```

# User

```
select current_user;      // to show current active user.
\du                       // to display all user

CREATE USER newuser WITH PASSWORD 'password';    // create new user.
ALTER USER username WITH PASSWORD 'newpassword'; // to change user password
GRANT ALL PRIVILEGES ON DATABASE your_database TO your_user; // to grant all privileges to user.

DROP USER username;           // to delete user
DROP USER demouser CASCADE;   // to delete forcely if it owns some objects
```

# Connect Server Database to local Machine

```
/etc/postgresql/<version>/main/postgresql.conf:
listen_addresses = '\*' // #listen_addresses = 'localhost,174.138.30.75'
ssl = off               // ssl = on :default

/etc/postgresql/<version>/main/pg_hba.conf:
host all all 0.0.0.0/0 // uncomment this line

$ sudo systemctl restart postgresql
or
$ sudo service postgresql restart
```

# Import/Export Database

### Export Database from Postgres

```
pg_dump -U <postgres_user> -h localhost -p 5432 <database_name> > <download_database_name.sql>
Ex: pg_dump -U postgres -h localhost -p 5432 trimerp > trimerp_dump.sql
```

### Import Database

```
# Make sure <database_file>.sql file in /var/lib/postgresql

psql -U <postgres_user> -d <database_name> -f <database_file>.sql
Ex: psql -U postgres -d trimerp -f trimerp_dump.sql
```

### Download File from remote machine.

```
scp <user_name>@<server_id>:<path> <download_path>
Ex: scp root@174.138.30.75:/root/trimerp_dump.sql .
```
