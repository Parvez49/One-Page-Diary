# Go
Statically typed, Fast run time, Compiled, Fast compile time, Supports concurrency through goroutines and channel, Does not support classes and objects and inheritance, Has automatic garbage collection.

---
A Go file consists of the following parts:
```
package main
import ("fmt")

func main() {
  fmt.Println("Hello World!")
}
```

- Package declaration: every program is part of a package.
- Import packages
- Functions
- Statements and expressions

### variable and data type
- variable declaration: var variablename type = value,  variablename := value
- var a string, var b int, var c bool, all has default value initially '', 0, false
- var Can be used inside and outside of functions, := Can only be used inside functions.
- const CONSTNAME type = value
- default int size base on pc architecture 32 or 64 bit.
- singned int: int8, int16, int32, int64; unsigned int: uint8, uint16, uint32, uint64;
- float has two keywords: fload32, fload64, default float64
- array: var array_name = [length]datatype{values}, array_name := [...]datatype{values}
- Slices:
  - slice_name := []datatype{values}, slice can grow and shrink
  - var myarray = [length]datatype{values}; myslice := myarray[start:end]
  - slice_name := make([]type, length, capacity), If the capacity parameter is not defined, it will be equal to length.
  - slice_name = append(slice_name, element1, element2, ...), append elements to the end of a slice
  - slice3 = append(slice1, slice2...), Append One Slice To Another Slice

### print
- Print() function prints its arguments with their default format.
- Println() added whitespace between the arguments and new line is added at the end.
- Printf() function first formats its argument: fmt.Printf("i has value: %v and type: %T\n", i, i)
- %% 	Prints the % sign
- %#v 	Prints the value in Go-syntax format
- other fomatting: https://www.w3schools.com/go/go_formatting_verbs.php

### Condition and loop
- condition
  ```
  if condition1 {
     // code to be executed if condition1 is true
  } else if condition2 {
     // code to be executed if condition1 is false and condition2 is true
  } else {
     // code to be executed if condition1 and condition2 are both false
  }
  ```

- loop
   ```
  for statement1; statement2; statement3 {
     // code to be executed for each iteration
  }
  for i:=0; i < 5; i++ {
    fmt.Println(i)
  }
  ```
- loop range
  ```
  for index, value := range array|slice|map {
     // code to be executed for each iteration
  }
  fruits := [3]string{"apple", "orange", "banana"}
  for idx, val := range fruits {
     fmt.Printf("%v\t%v\n", idx, val)
  }
  ```

### function
- ```
  func FunctionName() {
    // code to be executed
  }
  ```
- with parameters
  ```
  func FunctionName(param1 type, param2 type, param3 type) {
    // code to be executed
  }
  ```
- with return
  ```
  func FunctionName(param1 type, param2 type) type {
    // code to be executed
    return output
  }
  // named return value
  func myFunction(x int, y int) (result int) {
    result = x + y
    return
  }
  func myFunction(x int, y string) (result int, txt1 string) {
    result = x + x
    txt1 = y + " World!"
    return
  }

  ```

### Structures
- ```
  type struct_name struct {
    member1 datatype;
    member2 datatype;
    member3 datatype;
    ...
  }

  var obj1 struct_name
  obj1.member1 = <value>
  ```

  ### Maps
  ```
  var a = map[KeyType]ValueType{key1:value1, key2:value2,...}
  b := map[KeyType]ValueType{key1:value1, key2:value2,...}

  ```

  # Examples
  - Make Package initialization: go mod init <app_name>
  - Structure, Methods, Composition(Instead of Inheritance)
    ```
    type Address struct {
        City    string
        Country string
    }
    
    type User struct {
        Name    string
        Age     int
        Email   string
        Address // embedded
    }
    // Method with value receiver
    func (u User) Display() {
        fmt.Println("----- User Profile -----")
        fmt.Println("Name:", u.Name)
        fmt.Println("Age:", u.Age)
        fmt.Println("Email:", u.Email)
        fmt.Println("Location:", u.City, "-", u.Country)
    }
    // Method with value receiver
    func (u User) IsAdult() bool {
        return u.Age >= 18
    }
    u := User{
            Name:  "Parvez Hossen",
            Age:   24,
            Email: "ph.cse.bd@gmail.com",
            Address: Address{
                City:    "Cumilla",
                Country: "Bangladesh",
            },
        }

    u.Display()
    ```
  - Interfaces & Polymorphism
    - An interface is a type that defines a set of method signatures.
    - Intefaces similar with python abstract method.
    ```
    type Notifier interface {
        Notify() string
    }
    
    type Email struct {
        Address string
    }
    
    func (e Email) Notify() string {
        return "Sending email to " + e.Address
    }
    
    type SMS struct {
        Number string
    }
    
    func (s SMS) Notify() string {
        return "Sending SMS to " + s.Number
    }
    
    func sendNotification(n Notifier) {
        fmt.Println(n.Notify())
    }
    
    func main() {
        e := Email{Address: "parvez@example.com"}
        s := SMS{Number: "0123456789"}
    
        sendNotification(e)
        sendNotification(s)
    }

    ```

  - Goroutines (Concurrency)
    - Concurrency:  managing multiple tasks at one core or thread.
    - Parallelism:  managing multiple tasks at the same exact time (requires multiple CPU cores).
    - lightweight thread managed by the Go runtime.
    ```
    package main
    
    import (
    	"fmt"
    	"sync"
    	"time"
    )
    
    func sendEmail(wg *sync.WaitGroup, to string) {
    	defer wg.Done()
    	time.Sleep(2 * time.Second)
    	fmt.Println("📧 Email sent to:", to)
    }
    
    func sendSMS(wg *sync.WaitGroup, number string) {
    	defer wg.Done()
    	time.Sleep(1 * time.Second)
    	fmt.Println("📱 SMS sent to:", number)
    }
    
    func main() {
    	var wg sync.WaitGroup
    	wg.Add(2) // We have 2 goroutines to wait for
    
    	go sendEmail(&wg, "parvez@example.com")
    	go sendSMS(&wg, "+8801568079422")
    
    	fmt.Println("✅ Sending notifications...")
    	wg.Wait() // Wait for both goroutines to finish
    	fmt.Println("🎉 All notifications sent!")
    }

    ```

- Channels
  - A channel is a typed conduit through which goroutines can send and receive values between goroutines.
  - They provide safe communication and synchronization between concurrent goroutines.
  - 
