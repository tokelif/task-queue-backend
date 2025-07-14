# task-queue-backend

A modern, scalable, and secure backend task queue infrastructure. Jobs are queued via API, processed asynchronously by a worker, and results can be tracked. The entire architecture is easy to deploy with Docker Compose.

---

## Architecture Components

- **API (Flask):** Endpoints for adding tasks, checking status, and health checks.
- **Worker (Python):** Consumes tasks from the queue, processes them, and saves results to the database.
- **RabbitMQ:** Durable and asynchronous message queue.
- **PostgreSQL:** Relational database for storing all tasks and results.
- **Docker Compose:** Orchestrates all services with a single command.

```
User <--> API (Flask) <--> RabbitMQ <--> Worker <--> PostgreSQL
```

---

## Installation & Requirements

### System Requirements

- **Docker** (20.10+)
- **Docker Compose** (v2 or v1.29+)
- **Git**

#### Linux (Ubuntu):

```bash
sudo apt update
sudo apt install git docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo apt install docker-compose-plugin -y   # Compose V2 recommended
# For classic v1:
# sudo apt install docker-compose -y
```

#### MacOS & Windows:

- Download and install [Docker Desktop](https://docs.docker.com/desktop/).

---

### Clone the Repository

```bash
git clone https://github.com/tokelif/task-queue-backend.git
cd task-queue-backend
```

---

### Start the Services

```bash
docker compose up --build
# or for classic Docker Compose:
docker-compose up --build
```

Services:
- **API:** [http://localhost:5000](http://localhost:5000)
- **RabbitMQ UI:** [http://localhost:15672](http://localhost:15672) (user: guest, pass: guest)
- **PostgreSQL:** localhost:5432

---

## Usage

Once services are running, you can interact with the API as follows.

### Add a Task

```bash
curl -X POST http://localhost:5000/add_task \
     -H "Content-Type: application/json" \
     -d '{"task_type": "ping", "task_data": "8.8.8.8"}'
```

Example response:
```json
{
  "task_id": "a1b2c3d4-...",
  "status": "pending"
}
```

### Check Task Result

```bash
curl http://localhost:5000/get_task/a1b2c3d4-...
```

Example response:
```json
{
  "task_id": "a1b2c3d4-...",
  "task_type": "ping",
  "task_data": "8.8.8.8",
  "status": "completed",
  "result": "PING 8.8.8.8 ..."
}
```

### Health Check

```bash
curl http://localhost:5000/
```

---

## API Endpoints

| Method | Endpoint              | Description           |
| ------ | --------------------- | ---------------------|
| POST   | `/add_task`           | Add a task           |
| GET    | `/get_task/<task_id>` | Get task status/info |
| GET    | `/`                   | Health check         |

---

## Task Types

| Task Type           | Description                                                        | `task_data` Example                                      |
| ------------------- | ------------------------------------------------------------------ | -------------------------------------------------------- |
| ping                | Pings an IP or hostname                                            | `"8.8.8.8"` or `"google.com"`                            |
| dns_lookup          | Resolves a domain to IP addresses                                  | `"google.com"`                                           |
| katana              | Crawls URLs using [katana](https://github.com/projectdiscovery/katana) | `"https://wikipedia.com"`                            |
| online_word_count   | Counts occurrences of a word on a web page                         | `{"url": "...", "word": "..."}` (JSON string)            |
| command             | Executes arbitrary shell commands                                  | `"ls -la /tmp"`                                          |
| http_get            | Fetches content from a URL (first 1000 chars)                      | `"https://example.com"`                                  |

---

## Example Task Submissions

Example `curl` commands for different task types:

```bash
# Shell command
curl -X POST http://localhost:5000/add_task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"command","task_data":"ls -l"}'

# Ping
curl -X POST http://localhost:5000/add_task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"ping","task_data":"8.8.8.8"}'

# HTTP GET
curl -X POST http://localhost:5000/add_task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"http_get","task_data":"https://en.wikipedia.org/wiki/Python_(programming_language)"}'

# DNS Lookup
curl -X POST http://localhost:5000/add_task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"dns_lookup","task_data":"youtube.com"}'

# Online Word Count
curl -X POST http://localhost:5000/add_task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"online_word_count","task_data":"{\"url\": \"https://en.wikipedia.org/wiki/Python_(programming_language)\", \"word\": \"python\"}"}'

# Katana URL crawl
curl -X POST http://localhost:5000/add_task \
  -H "Content-Type: application/json" \
  -d '{"task_type":"katana","task_data":"https://wikipedia.com"}'
```

---

## Configuration

All environment variables are set via docker-compose:

```env
DB_HOST=db
DB_NAME=task_queue_db
DB_USER=user
DB_PASSWORD=user
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
```

Default ports:
- API: **5000**
- PostgreSQL: **5432**
- RabbitMQ: **5672** (15672 for UI)

---

## Dependencies

### Python Packages

- Flask
- Werkzeug
- psycopg2-binary
- pika
- requests
- beautifulsoup4

### Worker Dockerfile System Dependencies

- wget, unzip (for downloading katana)
- nmap, iputils-ping (for network tasks)
- libpq-dev, gcc (for psycopg2)
- katana (binary, placed in `/usr/local/bin/katana`)

---

## Troubleshooting

- **Services not starting:** Is Docker running? Any port conflicts? Check logs with `docker compose logs`.
- **psycopg2 installation error:** Make sure `libpq-dev` and `gcc` are installed in the worker Dockerfile.
- **Katana not found:** Is the katana download URL up to date? Check `mv/chmod` steps in the Dockerfile.
- **init.sql error:** Example schema:
    ```sql
    CREATE TABLE tasks (
      task_id TEXT PRIMARY KEY,
      task_type TEXT,
      task_data TEXT,
      status TEXT,
      result TEXT
    );
    ```
- **Worker does not start:** Check RabbitMQ and DB connections. Ensure all required Python packages are installed.
- **Docker permissions error:** Use `sudo` or add your user to the docker group:
    `sudo usermod -aG docker $USER` (logout/login required)

---
