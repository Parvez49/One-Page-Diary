## C++
 is an object-oriented programming language created by Bjarne Stroustrup. It was released in 1985. C language was developed by Dennis Ritchie.

## Difference between C and C++:
 C is a Procedural Oriented Programming (POP) language, whereas C++ language supports Object Orientation. Additionally, C++ supports features like templates, inheritance, function overloading, virtual functions, friend functions, and references. These features are not supported in C.

##  Compilation Time and Run Time:
 The time Compiler takes for compiling a piece of code is called Compilation Time of the code. The time taken by the program to run is called Run Time.

## exception handling:
 Exception handling is used when some exception is encountered in the program. Three keywords are used for exception handling: try, catch, throw.

## Operator overloading: 
 Manipulating the operations of a pre-existing operator to achieve different operations.

## polymorphism.
```
 If an object follows polymorphism, then it acts differently in different conditions. There are two types of polymorphism:

    Compile-time polymorphism (static binding)
    Run-time polymorphism (dynamic binding)
```

## Function overloading:
 the concept of having many functions with the same name. These functions should have different parameters for different types of functioning. Compile-time polymorphism is also known as static polymorphism. The polymorphism which is implemented at the compile time is known as compile-time polymorphism. Method overloading is an example of compile-time polymorphism.

## Function overriding:
 Re-defining the member function of base class in the derived class is function overriding. Runtime polymorphism is also known as dynamic polymorphism. Function overriding is an example of runtime polymorphism.

## Encapsulation 
 is a technique of wrapping the data members and member functions in a single unit. It binds the data within a class, and no outside method can access the data. If the data member is private, then the member function can only access the data.

## Abstraction:
 Abstraction is used to hide the internal implementations and show only the necessary details to the outer world. Data abstraction is implemented using interfaces and abstract classes in C++.

## class in C++:
 A class is a collection of different variables and different functions. The variables are called data members and the functions are called member functions.

## Constructor:
 A constructor is a special member function of a class. When we declare an object, it initializes the data member.

## Copy Constructor:
 A Copy Constructor is a member function of a class. When called while creating a new object of the class, it initializes the object using another object of the same class. In order to use a Copy Constructor, there should be already an existing object of that class.
 ```
 class Copy
 {
	private:
		int a;
	public:
		Copy(int z)
		{
			a=z;
		}
		Copy( Copy &x)
		{
			a=x.a;
		}
		void print()
		{
			cout<<“Value of ‘a’ is ”<<a<<endl;
		}
 };
 int main()
 {
	Copy p(10);
	p.print();
	Copy q = p;
	q.print();
 }
 ```

## destructor:
 A destructor is a special member function. The Destructor destructs the object and frees up space.

##  inner class:
 A nested class is a class which is declared inside another class.

## Difference between structure and class:
 The variables of the structures are public, whereas the data member of the class can be made as private.

## Inheritance:
 Inheritance is the feature in which an object acquires the properties of another class. 
 ```
    Single inheritance : there is one derived class and one base class.
    Multiple inheritance : a class is derived from another derived class.
    Multi-level inheritance : This is when a class can be derived with more than one parent class.
    Hierarchical inheritance : many classes are derived from a single parent class.
    Hybrid inheritance : This is a combination of more than one inheritance.
 ```

## Template:
 A template is a method for creating generic classes and generic functions.

## Access specifiers:
 ```
 Access Specifiers define the accessibility of the members of the class.

    Private – they are only accessible from inside of the class
    Protected – like private specifiers but with an extra feature — they are also accessible in derived classes
    Public – they are accessible from both inside and outside the class
 ```

## Friend function:
 A friend function to a class has access to all the members of the class, even the private ones. We declare it outside the class. Friend function acts as a friend of the class. It can access the private and protected members of the class. The friend function is not a member of the class, but it must be listed in the class definition. The non-member function cannot access the private data of the class. 
 ```
     class sample  
    {  
       // data members;  
     public:  
    friend void abc(void);  
    };  
 ```

## Virtual function:
 A virtual function is a function declared as a member function of a class, but its definition is inside its derived class.

## Friend Class:
```
 If a class is mentioned as a friend class to another class, then it can access private and protected members of the other class.
 
 class ClassA
 {
	private:
		int a;
	public:
		ClassA()
		{
			a=10;
		}
        ~ClassA()
		{
			a=10;
		}
		friend class FriendClass;
 };
 class FriendClass
 {
	private:
		int b;
	public:
		void printClassA(ClassA& p)
		{
			cout<<“a=”<<p.a<<endl;
		}
 };
 int main()
 {
	ClassA x;
	FriendClass y;
	y.printClassA();
	return 0;
 }
```

## Map uses BST as its data structure.

## How is ‘final’ used?
 We add ‘final’ after the function name at the time of declaring to prevent overriding in derived classes.

## std:
 is also known as Standard or it can be interpreted as a namespace. The command “using namespace std” informs the compiler to add everything under the std namespace and inculcate them in the global namespace. This all inculcation of global namespace benefits us to use “cout” and “cin” without using “std::_operator_”.

## What is the difference between new() and malloc():
 new() is a preprocessor while malloc() is a function.