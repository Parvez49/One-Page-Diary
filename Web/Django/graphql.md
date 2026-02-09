
## GraphQL
- GraphQL enforces a strict separation between read and write models, unlike DRF serializers which mix both.
- GraphQL exists to fix the pain points of REST when apps get complex.
  - Over-fetching: get more data you need, serializer response fixed fields.
  - Under-fetching: need multiple requests to build one screen.
  - ```
    GET /users/1
    GET /users/1/orders
    GET /orders/5/items
    ```
  - All queries go through one endpoint. Easier auth, Easier versioning, Easier gateway setup.
  
### Types
- is used for read data
- Expose the Django User model as a GraphQL type.
- strawberry_django will automatically generate resolvers for relational fields.
- ```
  @strawberry.django.type(User)
  class UserType:
      id: auto
      username: auto # Strawberry infers the field type from the Django model
  ```
- 
