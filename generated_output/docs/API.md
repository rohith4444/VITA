# API Documentation

## Endpoints

- `GET /tasks`: Returns a list of all tasks
- `POST /tasks`: Creates a new task. Requires a JSON body with `title`, `description`, and `dueDate`
- `PUT /tasks/:id`: Updates a task. Requires a JSON body with `title`, `description`, and `dueDate`
- `DELETE /tasks/:id`: Deletes a task

## Parameters

- `id`: The ID of the task

## Responses

- `200 OK`: The request was successful
- `201 Created`: A new task was created successfully
- `204 No Content`: The task was deleted successfully
- `400 Bad Request`: The request was invalid or could not be understood by the server
- `404 Not Found`: The requested resource could not be found