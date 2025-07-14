import pika
import time
import logging
import json
import psycopg2
import os
import subprocess
import requests
import socket

# Configures logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables set up database and RabbitMQ connections. Defaults match Docker service names.
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "task_queue_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "user")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

# Connects to PostgreSQL database
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Handles tasks from RabbitMQ
def process_task(channel, method, properties, body):
    logger.info(f"Received task: {body}")
    data = json.loads(body)
    task_id = data.get("task_id")
    task_type = data.get("task_type")
    task_data = data.get("task_data")
    result = None

    try:
        if task_type == "ping":
            try:
                # Executes a ping command with 1 attempt and 3-second timeout
                process = subprocess.run(
                    ["ping", "-c", "1", "-W", "3", task_data],
                    capture_output=True, text=True
                )
                result = process.stdout if process.returncode == 0 else process.stderr
            except Exception as error:
                result = f"Ping failed: {error}"

        elif task_type == "dns_lookup":
            try:
                # Resolves a domain name to IP addresses using socket
                ip_list = socket.gethostbyname_ex(task_data)
                result = f"IP addresses for {task_data}: {', '.join(ip_list[2])}"
            except Exception as error:
                result = f"DNS lookup failed: {error}"

        elif task_type == "katana":
            try:
                logger.info(f"Running katana for URL: {task_data}")
                process = subprocess.run(
                    ["katana", "-u", task_data, "-o", "katana_output.txt"],
                    capture_output=True, text=True, timeout=300
                )
                logger.info(f"Katana process return code: {process.returncode}")
                logger.info(f"Katana stdout: {process.stdout}")
                logger.info(f"Katana stderr: {process.stderr}")
                if process.returncode == 0:
                    with open("katana_output.txt") as file:
                        urls = file.readlines()
                    url_count = len(urls)
                    result = f"Found {url_count} URLs at {task_data}"
                else:
                    result = f"Katana error: {process.stderr}"
                    logger.error(result)
            except Exception as error:
                result = f"Katana failed: {error}"
                logger.error(result)

        elif task_type == "online_word_count":
            try:
                # Counts occurrences of a word in a webpage's text
                data_dict = json.loads(task_data)
                url = data_dict.get("url")
                word = data_dict.get("word")
                if not url or not word:
                    result = "Both url and word are required"
                else:
                    response = requests.get(url, timeout=10)
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        text = soup.get_text(separator=' ')
                    except ImportError:
                        text = response.text
                    count = text.lower().count(word.lower())
                    result = f"The word '{word}' appears {count} times at {url}"
            except Exception as error:
                result = f"Online word count failed: {error}"

        elif task_type == "command":
            try:
                # Executes a shell command and captures its output
                process = subprocess.run(task_data, shell=True, capture_output=True, text=True)
                result = process.stdout if process.returncode == 0 else process.stderr
            except Exception as error:
                result = f"Command failed: {error}"

        elif task_type == "http_get":
            try:
                # Fetches a webpage and returns the first 1000 characters
                response = requests.get(task_data, timeout=10)
                result = response.text[:1000]
            except Exception as error:
                result = f"HTTP GET failed: {error}"

        # Updates task status and result in the database
        logger.info(f"Updating DB for task_id={task_id} with status='completed' and result length={len(str(result)) if result else 0}")
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE tasks SET status = %s, result = %s WHERE task_id = %s",
                    ("completed", result, task_id)
                )
                logger.info(f"DB update rowcount: {cursor.rowcount}")
                conn.commit()
            conn.close()
            logger.info(f"Task completed: {task_id}")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as db_error:
            logger.error(f"DB update error for task_id={task_id}: {db_error}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    except Exception as error:
        logger.error(f"Database error: {error}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# Runs the worker in a loop
def main():
    while True:
        try:
            logger.info("Attempting to connect to RabbitMQ...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()
            channel.queue_declare(queue='task_queue', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='task_queue', on_message_callback=process_task)
            logger.info("Worker started, listening for tasks...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ connection failed. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as error:
            logger.error(f"Unexpected error: {error}")
            time.sleep(5)

if __name__ == "__main__":
    main()

