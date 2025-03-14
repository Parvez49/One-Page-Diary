### 1. What is Nginx, and how does it differ from Apache?
  Nginx (pronounced "engine-x") is a high-performance web server, reverse proxy, load balancer, and HTTP cache. It is known for handling high concurrency with low memory usage.

### 2. What are the key features of Nginx?
    - High Performance: Can handle thousands of concurrent connections efficiently.
    - Reverse Proxy & Load Balancing: Distributes traffic to backend servers.
    - Static Content Serving: Optimized for serving static files like images, CSS, and JavaScript.
    - Security Features: Supports SSL/TLS termination, rate limiting, and access control.
    - Caching Mechanism: Reduces backend load.
    - WebSocket Support: Suitable for real-time applications.

### 3. how does Nginx differ from Apache?
Nginx (Event-Driven Architecture)
- Nginx operates with a single worker process (or multiple workers if configured).
- A single worker process can handle multiple concurrent requests at the same time using an event loop.
- When 10 requests per second arrive(How Nginx Handle 10 Requests per Second):
    - Nginx does not create a new process/thread for each request.
    - Instead, the worker process handles all 10 requests asynchronously.
    - It efficiently manages I/O operations (like reading from disk, waiting for database responses) without blocking.
    - If configured with multiple worker processes, it distributes the load among them.
  
Apache (Process-Based Architecture)
- Suppose Apache is running 5 worker processes (using the Prefork or Worker MPM).
- Each worker process can handle one request at a time.
- When 10 requests arrive(How Apache Handle 10 Requests per Second if it has 5 process):
    - The first 5 requests are immediately processed.
    - The next 5 requests must wait until some processes finish.
    - Once a worker process completes its task, it picks up a new request from the queue.
    - If requests take longer to process, the queue builds up, increasing latency.
 
### 4. Mention what is the Master and Worker Processes in Nginx Server?
    - Master processes: It reads as well as evaluates configuration and maintains worker processes.
    - Worker processes: It actually does the processing of the requests.
      
