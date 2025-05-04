### Python code execution
 code -> compile to bytecode(.pyc) -> interprete machine code and run

### Closure in Python
closure is a function object that remembers values in enclosing scopes even if those scopes are no longer present in memory.
A closure happens when:
- A nested function (function inside another function) is defined.
- The inner function refers to variables from the enclosing scope.
- The enclosing function returns the inner function.

```
# [*]Enclosing Scope
def outer_func():
   x = 90
  
   def inner_func():
      print("Value of x from inner::",x)
 
   inner_function()

outer_func()

[*]Output
Value of x from inner::90
```

## Python OOP Cheat Sheet: Book Class

### Class Definition
```
from typing import Dict, Union

class LibraryItem:
    def __init__(self, title: str) -> None:
        self.title = title

    def get_details(self) -> None:
        print(f"Library Item: {self.title}")

    def borrow(self) -> None:
        print(f"Borrowed item: {self.title}")

    def return_item(self) -> None:
        print(f"Returned item: {self.title}")

class Book(LibraryItem):
    total_books = 0
    distinct_books = 0

    def __init__(self, book_name: str, copies: int) -> None:
        self.book = book_name
        self.copies = copies
        Book.total_books += copies
        Book.distinct_books += 1

    # Instance Method
    def borrow(self) -> None:
        if self.copies > 0:
            self.copies -= 1
            Book.total_books -= 1
            print(f"You borrowed '{self.book}'. Copies left: {self.copies}")
        else:
            print(f"'{self.book}' is currently unavailable.")

    def return_book(self) -> None:
        self.copies += 1
        Book.total_books += 1
        print(f"You returned '{self.book}'. Copies now: {self.copies}")

    def get_details(self) -> None:
        print(f"Book: {self.book}, Copies Available: {self.copies}")

    # Class Method
    @classmethod
    def library_book_stats(cls) -> None:
        print(f"Total copies of {cls.distinct_books} distinct books: {cls.total_books}")

    @classmethod
    def new_object_from_dict(cls, data: Dict[str, Union[str, int]]) -> "Book":
        return cls(data['book_name'], data['copies'])

    # Static Method
    @staticmethod
    def is_valid_book_data(data: Dict[str, Union[str, int]]) -> bool:
        if not isinstance(data, dict):
            return False
        required_keys = {'book_name', 'copies'}
        if not required_keys.issubset(data.keys()):
            return False
        if not isinstance(data['book_name'], str) or not isinstance(data['copies'], int):
            return False
        if data['copies'] <= 0:
            return False
        return True
```
### Example Usage
```
book_data = {"book_name": "Clean Code", "copies": 3}

if Book.is_valid_book_data(book_data):
    b1 = Book.new_object_from_dict(book_data)
    b1.get_details()
    b1.borrow()
    b1.return_book()
    Book.library_book_stats()
else:
    print("Invalid book data.")
```

### Four Pillars of OOP Demonstrated in Book Class
- Encapsulation 🔒: bundling data and methods that operate on that data within a class, and restricting direct access to some of the class's components. Variables like copies and book are only modified through methods (borrow_book, return_book), not directly exposed.
- Abstraction 🧠: Abstraction means hiding complex internal implementation and exposing only essential parts of the object’s behavior to the outside world. The is_valid_book_data() method hides validation logic, offering a simple interface for data checking. new_object_from_dict() abstracts how a Book object is created from a dictionary, which could come from user input, a database, or an API.
-Inheritance 🧬: Book inherits from LibraryItem, reusing and customizing base methods like get_details() and borrow().
- Polymorphism 🧩: borrow() and return_item() behave differently in Book compared to base LibraryItem.



### List
```
Create list
	*1.1d--->li=[0]*5 or li = [0 for i in range(N)]
	*2.1d--->pow2 = [2 ** x for x in range(10)]
	*1.2d---<li = [[0]*cols]*rows
	*2.2d--->li = [[0 for i in range(cols)] for j in range(rows)]
		arr=[]
		for i in range(rows):
    			col = []
    			for j in range(cols):
        			col.append(0)
    			arr.append(col)
		print(arr)
	#use 2.2 for creating 2d list and working with index
List method
li=['p','a','r',0,1,2,3,4]
	*li.append()  //adds an element to the end of the list
	*insert()--->insert an item at the defined index.  
		     'o' is inserted at index 3 (4th position)li.insert(3, 'v')

	*extend()--->adds all elements of a list to another list
	*sort()--->sort items in a list in ascending order
	*reverse()--->reverse the order of items in the list
	*remove()--->remove an item from the list. --->li.remove('v')
	*pop()   --->returns and removes an element at the given index
	*clear()--->removes all items from the list
	*index()--->returns the index of the first matched item
	*count()--->returns the count of the number of items passed as an argument
	*copy()--->returns a shallow copy of the list
```
##Difference strip() and split(): strip() is used to removed specefic character from strin. its may be whitespace, character, symbol etc
				  split() is to make sub string list break a string
