from flask import Flask, request, jsonify
import pika
import psycopg2
import uuid
import json
import os
import logging

# Creates the Flask application
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables configure database and RabbitMQ connections. Defaults apply if not set.
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "task_queue_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "user")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# Connects to PostgreSQL database
def get_db_connection():
    try:
        # Uses psycopg2 to connect to PostgreSQL with credentials from environment variables.
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as error:
        logger.error(f"Database connection failed: {error}")
        raise

# Connects to RabbitMQ
def get_rabbit_connection():
    try:
        # Uses pika to establish a RabbitMQ connection. Returns a connection object.
        return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    except pika.exceptions.AMQPConnectionError as error:
        logger.error(f"RabbitMQ connection failed: {error}")
        raise

# Adds a new task via POST request
@app.route("/add_task", methods=["POST"])
def add_task():
    try:
        # Retrieves JSON data from the request
        data = request.get_json()
        task_type = data.get("task_type")
        task_data = data.get("task_data")

        # Task type and data are mandatory. Returns 400 if missing.
        valid_task_types = ["command", "katana", "ping", "http_get", "dns_lookup", "online_word_count"]
        if not task_type or not task_data:
            return jsonify({"error": "Task type and task data are required"}), 400
        if task_type not in valid_task_types:
            return jsonify({"error": f"Invalid task type. Must be one of: {', '.join(valid_task_types)}"}), 400

        # Generates a unique task ID
        task_id = str(uuid.uuid4())

        # Inserts task into the database with "pending" status
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (task_id, task_type, task_data, status) VALUES (%s, %s, %s, %s)",
                (task_id, task_type, task_data, "pending")
            )
            conn.commit()
        conn.close()

        # Publishes task to RabbitMQ queue as JSON
        # durable=True and delivery_mode=2 ensure message persistence.
        with get_rabbit_connection() as connection:
            channel = connection.channel()
            channel.queue_declare(queue="task_queue", durable=True)
            message = {
                "task_id": task_id,
                "task_type": task_type,
                "task_data": task_data
            }
            channel.basic_publish(
                exchange="",
                routing_key="task_queue",
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )

        logger.info(f"Task added successfully: {task_id}")
        return jsonify({"task_id": task_id, "status": "pending"}), 201

    except Exception as error:
        logger.error(f"Error adding task: {error}")
        return jsonify({"error": "Failed to add task"}), 500

# Retrieves task status by task ID
@app.route("/get_task/<task_id>", methods=["GET"])
def get_task(task_id):
    try:
        # Queries the database for task details using the provided task ID
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id,))
            task = cursor.fetchone()
        conn.close()

        if task:
            return jsonify({
                "task_id": task[0],
                "task_type": task[1],
                "task_data": task[2],
                "status": task[3],
                "result": task[4]
            }), 200
        return jsonify({"error": "Task not found"}), 404

    except Exception as error:
        logger.error(f"Error retrieving task: {error}")
        return jsonify({"error": "Failed to retrieve task"}), 500

# Provides a health check for the API
@app.route("/")
def index():
    return jsonify({"message": "API is running"})

if __name__ == "__main__":
    # Starts the Flask app, listening on all interfaces at port 5000
    app.run(host="0.0.0.0", port=5000)
