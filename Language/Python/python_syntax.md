### Python code execution
- Python source code
  ```
	# hello.py
	print('hello world!')
  ```
- Calls the Python interpreter: python hello.py. Sends source file to interpreter(CPython).
- CPython reads the file
  - The interpreter opens hello.py and reads the text.
  - It converts the text into an Abstract Syntax Tree (AST).
  - Example for print('hello world!')
    ```
		Module
		  Expr
		    Call
		      Name: print
		      Args: Constant: 'hello world'
    ```
- Compilation to bytecode: CPython compiles the AST into bytecode, which is a lower-level, platform-independent representation of code.
- Bytecode is something like:
  ```
	LOAD_NAME                'print'
	LOAD_CONST               'hello world'
	CALL_FUNCTION            1
	POP_TOP
  ```
  - This bytecode can be stored as a .pyc file (in __pycache__) for faster execution next time.
    
- Execution by the Python Virtual Machine (PVM)
  - CPython has a virtual machine (interpreter loop) called PVM.
  - The PVM executes bytecode instruction by instruction.
    - LOAD_NAME 'print' → load the print function into memory
    - LOAD_CONST 'hello world' → load the string
    - CALL_FUNCTION 1 → call print('hello world')
    - POP_TOP → remove the result from the stack

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


## Descriptor
- A descriptor is any object that defines one or more of the methods __get__, __set__, __delete__, __set_name__.
- Adescriptor object describes how another object’s attribute should behave when read, write, or delete it.
- ```
  class PositiveNumber:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(f"{self.name} must be positive")
        instance.__dict__[self.name] = value
	
	
	class BankAccount:
	    balance = PositiveNumber()  # Descriptor handles validation
	
	    def __init__(self, balance):
	        self.balance = balance

  	class Product:
	    price = PositiveNumber()
	
	class Employee:
	    salary = PositiveNumber()
	
		
	
	acct = BankAccount(100)
	acct.balance = 200   # Works
	# acct.balance = -50  # Raises ValueError automatically

	```
- One descriptor can be used in multiple classes without rewriting logic.
- __get__(self, instance, owner): Called when the attribute is accessed acct.balance
- __set__(self, instance, value): Called when the attribute is assigned acct.balance = 200
- Types of Descriptors
  - Data Descriptor: Implements __set__ or __delete__ → overrides instance dictionary
  - Non-data Descriptor: Only implements __get__ → like @property without setter
 
## Multiprocessing
- Process → independent unit of execution (separate memory space). It uses it's own interpreter.
- Perfect for CPU-bound tasks (data crunching, data processing)
- Key Keyword of multiprocessing
  - Process:
  - Pool:
  - IPC(Inter-Process Communication):
  - Synchronization 

