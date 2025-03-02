# API Documentation

## Endpoints

1. **/tasks** - GET - Retrieve all tasks
2. **/tasks** - POST - Add a new task
   - Parameters: `title` (string), `description` (string), `due_date` (date)
3. **/tasks/:id** - GET - Retrieve a specific task
4. **/tasks/:id** - PUT - Update a specific task
   - Parameters: `title` (string), `description` (string), `due_date` (date), `status` (boolean)
5. **/tasks/:id** - DELETE - Delete a specific task

## Responses

- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error
