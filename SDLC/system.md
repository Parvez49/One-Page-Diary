### 1. Differences between Black Box Testing and White Box Testing

- White box testing techniques analyze the internal structures the used data structures, internal design, code structure, and the working of the software. White box testing can be done for different purposes. The three main types are:
  - Unit Testing
  - Regression Testing
  - Nonfunctional Testing (NFT)
- Black box testing is mainly focused on testing the functionality of the software, ensuring that it meets the requirements and specifications.
  - Functional Testing
  - Non-functional testing
  - Regression Testing

### What is Application Scaling?
refers to the process of increasing or decreasing an application's capacity to handle more or fewer users, requests, and data loads efficiently. The goal of scaling is to maintain performance, reliability as demand changes.
- scaling ensures application can handle more users without slowing down or crashing.
- Vertical Scaling(scaling up): increase resources(RAM, CPU, or SSD) in a single server.
- Horizontal Scaling(scaling out): add more machines(servers) to distribute the load. It require load balancer.

### What is Tools(django) scalable?
- efficintly handle increased traffic and growing data loads when deployed properly.
- support horizontal and vertical scaling.


## Software Architecture:
### Event-Driven Architecture (EDA) 
  is a software design pattern where system components communicate through events instead of direct requests. In this architecture, events are captured and processed asynchronously, enabling loose coupling, high scalability, and real-time responsiveness.

How it works:
- Event Producers (Publishers): These are components that detech a change(state change, user action, sensor data, etc) and generate an event.
- Events Brokers(Message Queue/Streams): Events are sent to an event broker or message queue(Redis Streams, Kafka, RabbitMQ
- Event Consumers (Subscribers): This listen for specific events and take action when they occur.
- Django with celery is a example of event-driven architecture.

### Monolithic Architecture:
is a single unified codebase where all components of an application(UI, database, business logic, and background tasks) are tightly integrated into a single deployable unit. A monolithic application typically has:
  - Presentation Layer (UI): Frontend (React, Next.js)
  - Business Logic Kayer: Application logic, service functions, etc.
  - Data Access Layer: ORM, database queries etc.
  - Database: A centralized database
  - All these layers within the same application and are deployed together.


