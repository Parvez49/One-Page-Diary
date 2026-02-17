### BASIC QUERY STRUCTURE
-
  ```
    SELECT column1, column2
    FROM table_name
    WHERE condition
    GROUP BY column
    HAVING condition
    ORDER BY column ASC|DESC
    LIMIT n OFFSET m;  // OFFSET m: skip first m rows, LIMIT n: select n rows from offset m.
  ```
- Execution order
  ```
    FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
  ```
- Constraints and keys: PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK, DEFAULT
- Aggregate function: COUNT(), SUM, AVG, MIN, MAX
- Date and time
  ```
    CURRENT_DATE
    CURRENT_TIMESTAMP
    DATEDIFF(date1, date2)
    DATE_ADD(date, INTERVAL 1 DAY)
  ```
- String functions
  ```
    CONCAT(first_name, ' ', last_name)
    LOWER(name)
    UPPER(name)
    LENGTH(name)
    SUBSTRING(name, 1, 5)
    TRIM(name)
  ```
- Join: Inner join, Left join, Right join
- Distinct and null handling:
  ```
    SELECT DISTINCT city FROM users;
    COALESCE(phone, 'N/A')
    NULLIF(a, b)
  ```
- CONDITIONAL LOGIC
  ```
    // CASE WHEN
    SELECT name,
       CASE
         WHEN salary > 5000 THEN 'High'
         ELSE 'Low'
       END AS category
    FROM employees;
  ```
- Window functions: Compute aggregates and rankings across related rows while preserving the original row structure.
  - ROW_NUMBER(): Assigns a unique sequential number to each row.
  - RANK(): Assigns the same rank to equal values but leaves gaps.
  - DENSE_RANK(): Assigns the same rank to equal values without gaps.
  - ```
      // ROW_NUMBER / RANK / DENSE_RANK
      SELECT salary,
         ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_number,
         RANK() OVER (ORDER BY salary DESC) AS rank,
         DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rnk
      FROM employees;
    
      salary row_number rank	dense_rank
        300      1      	1       1
        300	     2        1       1
        200	     3        3       2
        100	     4        4       3

      // LAG / LEAD  # LAG: Look at previous rows, LEAD: Look at next rows
      LAG(column, offset, default) OVER (ORDER BY column)
      LEAD(column, offset, default) OVER (ORDER BY column)    
    ```
- Set operation
  ```
    UNION        -- removes duplicates
    UNION ALL    -- keeps duplicates
  ```
- INSERT / UPDATE / DELETE / INDEX
  ```
    // INSERT
    INSERT INTO users (name, email)
    VALUES ('Parvez', 'test@gmail.com');
    
    // UPDATE
    UPDATE users
    SET salary = salary + 1000
    WHERE id = 1;
    
    // DELETE
    DELETE FROM users WHERE id = 5;

    // INDEX
    CREATE INDEX idx_user_email ON users(email);
  ```

### [Practice leetcode sql problems](https://leetcode.com/problem-list/wdplk2vm/)
  

