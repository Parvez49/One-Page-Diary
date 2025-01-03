# DBMS: 
 or a Database Management System is the computer software that enables storing, manipulating, managing and securing a large set of data.

## 1. SQL:
    stands for Structured Query Language. It is a language used to interact with the database,
    i.e to create a database, to create a table in the database, to retrieve data or update a table in the database, etc
    What is the difference between SQL and MySQL?
    SQL (Structured Query Language) is a standardized programming language used to manage and manipulate databases.
    MySQL is a specific relational database management system (RDBMS) that uses SQL as its querying language. MySQL is both a software and a server.

## What is RDBMS? How is it different from DBMS?
 RDBMS stands for Relational Database Management System. The key difference here, compared to DBMS, is that RDBMS stores data in the form of a collection of tables, and relations can be defined between the common fields of these tables.

## Database languages are:
 ```
 Data Definition Language (DDL) e.g., CREATE, ALTER, DROP, TRUNCATE, RENAME, etc. All these commands are used for updating the data that?s why they are known as Data Definition Language.
 Data Manipulation Language (DML) e.g., SELECT, UPDATE, INSERT, DELETE, etc. These commands are used for the manipulation of already updated data.
 DATA Control Language (DCL) e.g., GRANT and REVOKE. 
 Transaction Control Language (TCL) e.g., COMMIT, ROLLBACK, and SAVEPOINT.
 ```

## Three levels of data abstraction:
```
 Physical level: It is the lowest level of abstraction. It describes how data are stored.
 Logical level: It is the next higher level of abstraction. It describes what data are stored in the database and what the relationship among those data is.
 View level: It is the highest level of data abstraction. It describes only part of the entire database
```

## Normalization
 is a process of analysing the given relation schemas according to their functional dependencies. It is used to minimize redundancy and also used to minimize insertion, deletion and update distractions. Normalization is considered as an essential process as it is used to avoid data redundancy, insertion anomaly, updation anomaly, deletion anomaly.

There most commonly used normal forms are:

    First Normal Form(1NF)
    Second Normal Form(2NF)
    Third Normal Form(3NF)
    Boyce & Codd Normal Form(BCNF)

## Denormalization?
 Denormalization is the process of boosting up database performance and adding of redundant data which helps to get rid of complex data. Denormalization is a part of database optimization technique. This process is used to avoid the use of complex and costly joins.

## Relational Algebra
 is a Procedural Query Language which contains a set of operations that take one or two relations as input and produce a new relationship. Relational algebra is the basic set of operations for the relational model.

## Relational Calculus?

## Relational Calculus
 is a Non-procedural Query Language which uses mathematical predicate calculus instead of algebra. Relational calculus doesn't work on mathematics fundamentals such as algebra, differential, integration, etc. That's why it is also known as predicate calculus.

There is two type of relational calculus:

    Tuple relational calculus
    Domain relational calculus

