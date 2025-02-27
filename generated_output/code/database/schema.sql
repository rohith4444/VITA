CREATE TABLE Task (
    id UUID PRIMARY KEY NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    status VARCHAR(255) NOT NULL DEFAULT 'Pending'
);

CREATE INDEX idx_task_status_due_date ON Task(status, due_date);