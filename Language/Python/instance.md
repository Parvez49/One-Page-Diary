## Creational Design Patterns
 These patterns are focused on object creation mechanisms, trying to create objects in a manner suitable to the situation.

### Singleton Pattern
 ensures that a class has only one instance and provides a global point of access to it. This is useful when you need to control access to shared resources (e.g., a database connection or a logging class).
```
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Usage
s1 = Singleton()
s2 = Singleton()

print(s1 is s2)  # Output: True

```