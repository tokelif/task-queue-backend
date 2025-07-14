CREATE TABLE IF NOT EXISTS tasks (
    task_id VARCHAR PRIMARY KEY,
    task_type VARCHAR,
    task_data TEXT,
    status VARCHAR,
    result TEXT
);
