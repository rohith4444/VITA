# System Architecture

The application is divided into three main components: the frontend, the backend, and the database.

## Frontend

The frontend is built with React and Bootstrap. It consists of several components, including `Header`, `TaskList`, and `TaskItem`. The entry point for the frontend is `src/index.js`, which renders the `App` component.

## Backend

The backend is built with Node.js and Express.js. It handles requests from the frontend and interacts with the database. The entry point for the backend is `server.js`. The routes are defined in `src/routes/index.js`, and the task-related logic is handled by `src/controllers/tasksController.js`.

## Database

The database is built with MongoDB and PostgreSQL. The database configuration is defined in `db/index.js`, and the task model is defined in `src/models/Task.js`. The database schema and initial data are defined in the `migrations` directory.