# System Architecture

The application is divided into three main components: Frontend, Backend, and Database.

## Frontend

The frontend is built using React and Bootstrap. It consists of several components including `App.js` which is the main component, `Header.js` for the header section, `TaskList.js` for displaying the list of tasks, and `TaskItem.js` for individual tasks.

## Backend

The backend is built using Node.js and Express.js. It consists of `server.js` which is the main server file, `taskService.js` for handling task-related operations, `taskController.js` for controlling the flow of data, and `index.js` for routing.

## Database

The database is built using MongoDB and PostgreSQL. It consists of several migration files for setting up the database schema and tasks table, and a `database.yml` file for database configuration.

The application follows the MVC (Model-View-Controller) architecture. The frontend (View) interacts with the backend (Controller) which then interacts with the database (Model) to store and retrieve data.