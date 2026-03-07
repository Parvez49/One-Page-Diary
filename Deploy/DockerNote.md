# Docker Basic Concepts
## 1. Docker Architecture
### Components

**Docker Client**
- CLI tool (`docker`) used by developers.
- Sends commands to the Docker daemon via REST API.

**Docker Daemon (`dockerd`)**
- Background service responsible for:
  - Building images
  - Running containers
  - Managing volumes
  - Managing networks

**Docker Registry**
- Storage for Docker images.
- Examples:
  - Docker Hub
  - AWS ECR
  - GitHub Container Registry
  - Google Container Registry

Workflow:

Developer → Docker CLI → Docker Daemon → Registry → Container
---

# 2. Docker Image vs Container

| Feature | Docker Image | Docker Container |
|------|------|------|
| Type | Template | Running instance |
| State | Immutable | Mutable |
| Storage | Layered | Writable layer |
| Lifecycle | Build once | Run multiple times |

# 3. Docker Image Layers
Docker images are layered filesystem.

Example Dockerfile:
```
	FROM python:3.11
	WORKDIR /app
	COPY requirements.txt .
	RUN pip install -r requirements.txt
	COPY . .
```
Each instruction creates a new layer.
Benefits:
- Faster builds
- Layer caching
- Efficient storage

Check layers: `docker history image_name`

# 4. Docker Container Lifecycle
```
	Created    # docker create image
	   ↓
	Running    # docker start container
	   ↓
	Paused     # docker pause container
	   ↓
	Stopped    # docker stop container
	   ↓
	Deleted    # docker rm container
```

# 5. Docker Networking
Docker provides multiple networking modes.
- Bridge (Default)
  ```
	Containers communicate via internal network.
	Container A → Container B
	
	Example:
	
	docker network create mynetwork
	docker run --network=mynetwork nginx
  ```
- Host Network
  - Container shares host network.
  - faster but less isolation
  - docker run --network host nginx
- None Network
  - No network access.
  - docker run --network none nginx
- Overlay Network: Used in Docker Swarm for multi-host networking.

# 6. Docker Storage
Containers are ephemeral. Data disappears when container stops unless persisted.
- Bind Mount
  - Host directory mounted inside container.
  - easy access but host dependent
  - docker run -v /host/data:/container/data nginx
- Docker Volume
  - Docker-managed storage.
  - 	docker volume create myvolume
	    docker run -v myvolume:/data nginx
  - Portable, Secure, Better performance


# 7. Dockerfile
A **Dockerfile** is a script containing instructions to build a Docker image.

### Purpose
It documents **how to set up the application environment**.

### Example workflow
1. Write a `Dockerfile`
2. Docker Engine reads the file
3. Docker builds an **image**
4. Containers run from that image

Example structure:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

# 8. Docker Compose
Used to manage multi-container applications.

# 9. Docker Swarm
- **Docker Swarm** is Docker's **native clustering and orchestration tool**.
- It allows multiple Docker hosts to work together as a **single cluster**.

### Features
- Manages multiple **Docker daemons**
- Provides **load balancing**
- Handles **scaling containers**
- Enables **high availability**
-  Used for:
	- scaling
	- load balancing
	- cluster management
	- 		docker swarm init    # Initialize swarm
	  		docker service create nginx    # Deploy service
	  		docker service scale nginx=5    # Scale service:

# 10. Debugging Containers
	docker ps    # Check running containers
	docker ps -a    # ists running and stopped docker containers
	docker logs container_id    # Check logs
	docker exec -it container_id bash    # Execute inside container
	docker inspect container_id    # Inspect container
	docker images ls    # to show all images list
	
	
---

## Docker Image
- A **Docker Image** is like a **Class** in programming.
- It is a **read-only template** used to create containers.
- It contains everything needed to run an application:
  - Code
  - Runtime
  - Libraries
  - Environment variables
  - Configuration files
---

## Docker Container
- A **Docker Container** is like an **Object (Instance) of a Class**.
- It is a **running instance of a Docker Image**.
- Containers are:
  - Isolated
  - Lightweight
  - Fast to start
- Multiple containers can be created from the same image.

---

## Docker Daemon
- The **Docker Daemon (`dockerd`)** is a **persistent background service**.
- It manages all Docker operations.

### Responsibilities
- Listens for **Docker API requests**
- Builds Docker images
- Creates and runs containers
- Stops and removes containers
- Pulls images from registries (e.g., Docker Hub)
- Monitors container resources

In short, it **orchestrates the entire container lifecycle**.

---
   
### Mount (Bind Mount)
Mounting allows a container to access files from the host system.
#### Benefits
- Read and write files from the host
- Live code updates without rebuilding the image
- Useful during development
  
### Docker Volumes
Docker Volumes are persistent storage managed by Docker.
Think of them like external memory cards for containers.
- Why Volumes?
	- Data persists even if the container is removed
	- Safer than bind mounts
	- Managed directly by Docker
  


### Docker useful Command:
$ docker build -t image_name // to build image

$ docker run -d -p 4000:80 --name docker-container-name image_name
$ docker run -it ubuntu:14.04 /bin/bash 
$ docker run -v <HOST_DIRECTORY>:<CONTAINER_DIRECTORY>
$ docker run -it -v $(pwd):/mounted ubuntu:14.04 /bin/bash


# Docker Volume:
	$ docker volume ls
	$ docker-compose down -v
	$ docker volume create <volume_name>
	$ docker volume inspect <volume_name_or_id>    // to get detail information
	$ docker volume rm <volume_name_or_id> 
	$ docker volume prune                          // to remove unused volume
	



### Docker-compose.yml
- version: which version of docker-compose to use
- services: names of containers we want to ru
- build: steps describing the build process
- context: where the Dockerfile is located at to build the image
- ports: map ports from the host machine to the container
- volumes: map the host machine or a docker volume to the container
- environment : pass environment variables to the container
- depends_on : start the listed services before starting the current service

### Dockerfile
- FROM image_name — starts build by layering onto an existing image
- COPY host_path container_path — copies file or directory from host to the image
- RUN shell_command — runs a shell command in the image
- WORKDIR path — sets the current path in the image
- ENV variable value — sets the env variable equal to the value
- EXPOSE port — exposes a container port
- ENTRYPOINT ['shell', 'command'] — prefixes to CMD
- CMD ['shell', 'command'] —executes shell command at runtime




----------------------------------------------------------------

```
https://dev.to/thedevtimeline/add-mongodb-and-postgresql-in-django-using-docker-55j6
https://dev.to/karanpratapsingh/dockerize-your-react-app-4j2e
https://medium.com/@audretschjames/understanding-docker-as-if-it-were-a-gameboy-96c96392efbf
```

Kubernets: open source container orchestration tool.
