const taskService = require('../services/taskService');

const taskController = {
    createTask: (req, res) => {
        const { title, description, due_date } = req.body;
        taskService.createTask(title, description, due_date)
            .then(task => res.json(task))
            .catch(err => res.status(500).json(err));
    },
    markAsComplete: (req, res) => {
        const { id } = req.params;
        taskService.markAsComplete(id)
            .then(task => res.json(task))
            .catch(err => res.status(500).json(err));
    },
    getAllTasks: (req, res) => {
        const { status } = req.query;
        taskService.getAllTasks(status)
            .then(tasks => res.json(tasks))
            .catch(err => res.status(500).json(err));
    },
    deleteTask: (req, res) => {
        const { id } = req.params;
        taskService.deleteTask(id)
            .then(task => res.json(task))
            .catch(err => res.status(500).json(err));
    }
};

module.exports = taskController;