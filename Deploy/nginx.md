### 1. What is Nginx, and how does it differ from Apache?
  Nginx (pronounced "engine-x") is a high-performance web server, reverse proxy, load balancer, and HTTP cache. It is known for handling high concurrency with low memory usage.

### 2. What are the key features of Nginx?
    - High Performance: Can handle thousands of concurrent connections efficiently.
    - Reverse Proxy & Load Balancing: Distributes traffic to backend servers.
    - Static Content Serving: Optimized for serving static files like images, CSS, and JavaScript.
    - Security Features: Supports SSL/TLS termination, rate limiting, and access control.
    - Caching Mechanism: Reduces backend load.
    - WebSocket Support: Suitable for real-time applications.

### Nginx Directory Structure:
- /etc/nginx/
  - nginx.conf              # Main configuration file, Entry point for all config. Contains: http block, include directives, logging, worker processes, global settings etc.
  - sites-available/        # Stores all virtual host configuration files for domains. These configs are inactive by default — to activate one, must symlink it into sites-enabled/.
  - sites-enabled/          # Active Virtual Hosts, Holds symbolic links to active site configs from sites-available/.
  - conf.d/                  # Other conf files (auto-included by nginx.conf) Global Configuration Fragments: Global logging rules, Caching configurations, Load balancing pools, SSL settings.
  - snippets/                # Reusable config parts, Store partial configuration files that can be reused in multiple server blocks or locations.

### Domain Configuration
- Create Nginx config file
  - sudo nano /etc/nginx/sites-available/domain.com
    ```
      upstream proxy_block {
          server localhost:3001;
          keepalive 64;
      }
      
      server {
          server_name <domain.com>;
      
          location / {
              proxy_pass http://proxy_block;
      
              proxy_http_version 1.1;
              proxy_set_header Upgrade $http_upgrade;
              proxy_set_header Connection "upgrade";
      
              proxy_redirect off;
              proxy_set_header Host $host;
              proxy_set_header X-Forwarded-Proto $scheme;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Host $server_name;
          }
      
          listen 443 ssl; # managed by Certbot
          ssl_certificate /etc/letsencrypt/live/<domain.com>/fullchain.pem; # managed by Certbot
          ssl_certificate_key /etc/letsencrypt/live/<domain.com>/privkey.pem; # managed by Certbot
          include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
          ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
      
      }
      
      server {
          if ($host = <domain.com>) {
              return 301 https://$host$request_uri;
          } # managed by Certbot
      
      
          listen 80;
          server_name <domain.com>;
          return 404; # managed by Certbot
      
      
      }

    ```
 - Enable the config: ln -s /etc/nginx/sites-available/domain.com /etc/nginx/sites-enabled/
 - Test and reload Nginx: sudo nginx -t & sudo systemctl reload nginx
 - Stop a Running Domain:
   ```
     sudo rm /etc/nginx/sites-enabled/mydomain.com
     sudo nginx -t & sudo systemctl reload nginx
   ```

 - Load Balancing: Nginx forwards requests to multiple backend servers (e.g., on different ports or hosts) in a round-robin or other strategy.
   ```
     upstream app_servers {
        server 127.0.0.1:3001;
        server 127.0.0.1:3002;
    }
    
    server {
        location / {
            proxy_pass http://app_servers;
        }
    }
   
   defining multiple server lines in an upstream block is called load balancing.
   ```

### Nginx Caching (to cache backend API responses)
- Step 1: Define cache path
  ```
    /etc/nginx/conf.d/cache.conf
    proxy_cache_path /var/cache/nginx/api_cache_dir levels=1:2 keys_zone=api_cache:10m max_size=10m inactive=120m use_temp_path=off;
  ```
  - api_cache: name of cache zone
  - 10m: shared memory for storing metadata
  - 100m: max disk cache size
  - 60m: how long to keep unused cache

- Step 2: Enable caching in http block
  - /etc/nginx/nginx.conf
    ```
      ...
      map $arg_page $no_cache {
          1 0;
          2 0;
          3 0;
          4 0;
          5 0;
          default 1;
        }

	    include /etc/nginx/conf.d/*.conf;
      include /etc/nginx/sites-enabled/*;
      ...
    ```
- Step 3: Configuration api for caching
  - etc/nginx/snippets$ cat api_cache_list.conf
    ```
      location ^~ /api/incidents/v1/incidents/ {
          proxy_cache api_cache;
          proxy_cache_valid 200 0s;
          proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
          
          proxy_pass http://unix:/run/gunicorn_archive2024.sock;
          include proxy_params;
      
          proxy_cache_key "$scheme$host$request_uri$is_args$args";
      
          proxy_no_cache $no_cache;
          proxy_cache_bypass $no_cache;
      
          add_header X-Cache-Status $upstream_cache_status;
      }
    ```
- Step 4: Include in server block, /etc/nginx/sites-available/api.domain.com 
  ```
  	server {
	    server_name api.bangladesh2024.info;
	
	    location = /favicon.ico { access_log off; log_not_found off; }
	    location /static/ {
		alias /opt/Archive2024-Backend/staticfiles/;
	    }
	    location /media/ {
		root /opt/Archive2024-Backend/archive2024;
	    }
	    
	    include snippets/api_cache_list.conf;
	
	    location / {
		include proxy_params;
		proxy_pass http://unix:/run/gunicorn_archive2024.sock;
	    }
	
	    listen 443 ssl; # managed by Certbot
	    ssl_certificate /etc/letsencrypt/live/api.bangladesh2024.info/fullchain.pem; # managed by Certbot
	    ssl_certificate_key /etc/letsencrypt/live/api.bangladesh2024.info/privkey.pem; # managed by Certbot
	    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
	    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
	}
	
	server {
	    if ($host = api.bangladesh2024.info) {
		return 301 https://$host$request_uri;
	    } # managed by Certbot
	
	
	    listen 80;
	    server_name api.bangladesh2024.info;
	    return 404; # managed by Certbot
	}
  ```
    
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
      
