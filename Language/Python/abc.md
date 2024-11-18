
## Python Property decorator
```
 class Circle:
     def __init__(self, radius):
         self._radius = radius  # private attribute

     @property
     def radius(self):
         """Getter for radius."""
         return self._radius

     @radius.setter
     def radius(self, value):
         """Setter for radius with validation."""
         if value <= 0:
             raise ValueError("Radius must be positive!")
         self._radius = value

     @radius.deleter
     def radius(self):
         """Deleter for radius."""
         print("Deleting radius")
         del self._radius

## Using the Circle class
 circle = Circle(5)
 print(circle.radius)  # Access the radius (calls the getter)

 circle.radius = 10  # Set the radius (calls the setter)
 print(circle.radius)

 del circle.radius  # Deletes the radius (calls the deleter)
 print(circle.radius)

 circle.radius = 199
 print(circle.radius)

 ```

## Abstract Base Classes (ABCs)
 which are a way to define a common interface for a set of related classes and to enforce certain methods that must be implemented by any subclass, ensuring consistency across the hierarchy.

## Abstract class: 
 A class that contains one or more abstract methods, which are methods that are declared but not implemented. Abstract classes cannot be instantiated directly, and must be subclassed by concrete classes to be used.

## Abstract method: 
 A method that is declared in an abstract class but does not provide any implementation. The subclass is responsible for implementing these methods.

## Concrete subclass: 
 A subclass that provides implementations for all abstract methods from its parent class (if the parent is abstract) and can be instantiated.

```
from abc import ABC, abstractmethod

class Shape(ABC):
    @property
    @abstractmethod
    def area(self):
        """The area of the shape."""
        pass

    @property
    @abstractmethod
    def perimeter(self):
        """The perimeter of the shape."""
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    @property
    def area(self):
        return 3.14 * self.radius ** 2

    @property
    def perimeter(self):
        return 2 * 3.14 * self.radius
        
obj = Circle(5)
print(obj.area)
print(obj.perimeter)



class Square(Shape):
    def __init__(self, side_length):
        self.side_length = side_length

    @property
    def area(self):
        return self.side_length ** 2

    @property
    def perimeter(self):
        return 4 * self.side_length

```

## static and class method
```
class DataProcessor(ABC):
    @staticmethod
    @abstractmethod
    def process(data):
        """Process data in some way."""
        pass

    @classmethod
    @abstractmethod
    def from_file(cls, file_path):
        """Create an instance from a file."""
        pass

class CSVProcessor(DataProcessor):
    @staticmethod
    def process(data):
        return [line.split(',') for line in data]

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as file:
            data = file.readlines()
        return cls.process(data)

```

## Mixins
 A Mixin is a type of class used to add reusable functionality to other classes. A mixin class does not stand alone—it is meant to be inherited by other classes
```
class LoggingMixin:
    def log(self, message):
        print(f"Log: {message}")


class Car(LoggingMixin):
    def start(self):
        self.log("Starting the car.")
        print("Car is starting.")


class House(LoggingMixin):
    def open_door(self):
        self.log("Opening the door.")
        print("Door is open.")
```

## The Diamond Problem
 where a class inherits from two classes that both inherit from a common base class.
```
class A:
    def greet(self):
        print("Hello from A!")

class B(A):
    def greet(self):
        print("Hello from B!")

class C(A):
    def greet(self):
        print("Hello from C!")

class D(B, C):
    pass

# Usage
d = D()
d.greet()  # Which greet() method will be called? Hello from B!

# Python uses a method resolution order (MRO) to determine which method to call when there are multiple inheritance paths. In the example above, the method greet() from class B is called because D inherits from B first, followed by C.

```

## Composition and Inheritance

### Inheritance (Is-A Relationship): 
  is when a class (child) inherits properties and behaviors (methods) from another class (parent). This creates an "is-a" relationship between the child and the parent.

### Composition (Has-A Relationship)
 Composition is when one class contains instances of other classes as part of its state. This is an "has-a" relationship. Rather than inheriting functionality, a class can use other classes by including them as members.
 ```
class Engine:
    def start(self):
        return "Engine starting"

class Wheels:
    def rotate(self):
        return "Wheels rotating"

class Car:
    def __init__(self):
        self.engine = Engine()  # Car "has" an Engine
        self.wheels = Wheels()  # Car "has" Wheels
    
    def drive(self):
        return f"{self.engine.start()} and {self.wheels.rotate()}"

# Usage
car = Car()
print(car.drive())  # Output: Engine starting and Wheels rotating

 ```