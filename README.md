# task-queue-backend
---

## Description

`task-queue-backend` is a modern, scalable, and secure backend task queue infrastructure where jobs are queued via API, processed asynchronously by a worker, and results are tracked securely. The entire stack is orchestrated with Docker Compose for easy deployment.

---

## Architecture

* **API (Flask):** REST endpoints for submitting tasks, checking status, and health checks.
* **Worker (Python):** Consumes tasks from the queue, processes them, and stores results in the database.
* **RabbitMQ:** Asynchronous and durable message queue for task dispatching.
* **PostgreSQL:** Relational database for storing all tasks and results.
* **Docker Compose:** One-command orchestration of all services.

```
User <--> API (Flask) <--> RabbitMQ <--> Worker <--> PostgreSQL
```

---

## Installation & Requirements

### 1. System Requirements

* **Docker** (20.10+)
* **Docker Compose** (v2 or v1.29+)
* **Git**

#### **On Linux (Ubuntu):**

```bash
sudo apt update
sudo apt install git docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo apt install docker-compose-plugin -y   # Compose V2 recommended

# For classic v1:
# sudo apt install docker-compose -y
```

#### **On MacOS & Windows:**

* Install [Docker Desktop](https://docs.docker.com/desktop/).

---

### 2. Clone the Repository

```bash
git clone https://github.com/tokelif/task-queue-backend.git
cd task-queue-backend
```

---

### 3. Start the Services

```bash
docker compose up --build
# or classic
docker-compose up --build
```

* **API:** [http://localhost:5000](http://localhost:5000)
* **RabbitMQ UI:** [http://localhost:15672](http://localhost:15672) (user: guest, pass: guest)
* **PostgreSQL:** localhost:5432

---

## Usage

Once services are up, you can interact with the API as follows.

### Add a Task

```bash
curl -X POST http://localhost:5000/add_task \
     -H "Content-Type: application/json" \
     -d '{"task_type": "ping", "task_data": "8.8.8.8"}'
```

Response:

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

Response:

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

| Method | Endpoint               | Description          |
| ------ | ---------------------- | -------------------- |
| POST   | `/add_task`            | Add a task           |
| GET    | `/get_task/<task_id>`  | Get task status/info |
| GET    | `/`                    | Health check         |

---

## Task Types

* `ping`: Pings an IP or hostname.
* `dns_lookup`: Resolves a domain to IP addresses.
* `katana`: Uses [katana](https://github.com/projectdiscovery/katana) for URL crawling.
* `online_word_count`: Counts occurrences of a word on a given webpage. (Param: `{"url": "...", "word": "..."}`)
* `command`: Executes arbitrary shell commands.
* `http_get`: Fetches content from a URL (first 1000 characters).

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

* API: **5000**
* PostgreSQL: **5432**
* RabbitMQ: **5672** (15672 for UI)

---

## Dependencies

### Python Packages

* Flask
* Werkzeug
* psycopg2-binary
* pika
* requests
* beautifulsoup4

**System dependencies in the worker Dockerfile:**

* wget, unzip (for downloading katana)
* nmap, iputils-ping (for network tasks)
* libpq-dev, gcc (for psycopg2)
* katana (downloaded binary, placed in /usr/local/bin/katana)

---

## Examples

**Ping Task:**

```bash
curl -X POST http://localhost:5000/add_task \
     -H "Content-Type: application/json" \
     -d '{"task_type":"ping","task_data":"8.8.8.8"}'
```

**online_word_count Task:**

```bash
curl -X POST http://localhost:5000/add_task \
     -H "Content-Type: application/json" \
     -d '{"task_type": "online_word_count", "task_data": "{\"url\": \"https://example.com\", \"word\": \"Example\"}"}'
```

**dns_lookup Task:**

```bash
curl -X POST http://localhost:5000/add_task \
     -H "Content-Type: application/json" \
     -d '{"task_type": "dns_lookup", "task_data": "google.com"}'
```

---

## Troubleshooting

* **Services not starting:**
  * Is Docker running?
  * Any port conflicts?
  * Check logs with `docker compose logs` or `docker-compose logs`.

* **psycopg2 installation error:**
  * Make sure `libpq-dev` and `gcc` are installed in the worker Dockerfile.

* **Katana not found:**
  * Is the katana download URL up to date? Check Dockerfile `mv/chmod` steps.

* **init.sql error:**
  * Make sure your schema looks like:

    ```sql
    CREATE TABLE tasks (
      task_id TEXT PRIMARY KEY,
      task_type TEXT,
      task_data TEXT,
      status TEXT,
      result TEXT
    );
    ```

* **Worker does not start:**
  * Check RabbitMQ and DB connections.
  * Ensure all required Python packages are installed.

* **Docker permissions error:**
  * Use `sudo` or add your user to the docker group:
    `sudo usermod -aG docker $USER` (logout/login required)
---
