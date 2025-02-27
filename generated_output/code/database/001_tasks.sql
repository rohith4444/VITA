INSERT INTO Task (id, title, description, due_date, status) VALUES
    (uuid_generate_v4(), 'First task', 'This is the first task', '2022-12-31', 'Pending'),
    (uuid_generate_v4(), 'Second task', 'This is the second task', '2023-01-31', 'Pending');