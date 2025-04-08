
## Why Use a Connector Model Instead of ManyToManyField?
    1. Extra fields: You can add additional attributes to the relationship (e.g., quantity, status, etc.).
    2. Better control: You have more control over how relationships are managed, queried, and updated.
    3. Flexibility: The connector model provides more flexibility for complex relationships (e.g., filtering, sorting).
    4. Performance: You can optimize queries using select_related and prefetch_related, reducing the number of queries.
    5. Complex filtering: Easier to write complex queries and filters on relationships.
    6. Better database integrity: Allows you to manage the intermediate table structure, constraints, and indexing.
   
## When Might to Use ManyToManyField?
    1. The relationship between two models is purely many-to-many, and you don't need to store additional data on the relationship itself.
    2. when don’t need complex filtering, ordering, or aggregating based on the relationship.

## XSS (Cross-Site Scripting)
    XSS is a vulnerability where an attacker injects malicious scripts (usually JavaScript) into web pages viewed by other users.
