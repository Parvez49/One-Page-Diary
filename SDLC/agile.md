
Agile is a time boxed, iterative approach, to software development, 
to deliver the product incrementlly, instead of all at once.

Functionality --> Plan --> Implement --> Test --> Review

Review -- Satisfactory --> Yes --> build 
                       --> No  --> Plan 


## Coding Principles
1. DRY (Don't Repeat Yourself): Reduce code duplication and improve maintainability.
2. KISS (Keep It Simple, Stupid): Write code that is simple and easy to understand.
3. SOLID Principles (5 Object-Oriented Design Principles by Robert C. Martin)
   - S – Single Responsibility Principle (SRP): Each class should do one thing.
   - O – Open/Closed Principle: Software entities(classes, modules, functions, etc.) should be open for extension but closed for modification.
        ```
           ❌ Without Open/Closed Principle (Bad design)
           class PaymentProcessor:
              def pay(self, payment_type):
                  if payment_type == "credit_card":
                      print("Processing credit card payment")
                  elif payment_type == "paypal":
                      print("Processing PayPal payment")
            ✅ With Open/Closed Principle (Better design)
            class PaymentMethod:
                def pay(self):
                    raise NotImplementedError()
            
            class CreditCardPayment(PaymentMethod):
                def pay(self):
                    print("Processing credit card payment")


             class PaymentProcessor:
                  def process(self, method: PaymentMethod):
                      method.pay()

             Now, to add a new payment type:
             class ApplePayPayment(PaymentMethod):
                  def pay(self):
                      print("Processing Apple Pay payment")
            ```
  
    - L – Liskov Substitution Principle: Objects of a superclass should be replaceable with objects of its subclasses without breaking the application.
    - I – Interface Segregation Principle
    - D – Dependency Inversion Principle

 4. YAGNI (You Aren’t Gonna Need It): Don't implement something until it is necessary.
 5. Separation of Concerns (SoC): Divide a program into distinct sections, each handling a separate concern. MVC (Model-View-Controller) architecture separates data, UI, and logic.
