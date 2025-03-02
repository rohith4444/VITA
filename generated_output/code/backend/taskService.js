const Task = require('../models/Task');

const taskService = {
    createTask: (title, description, due_date) => Task.create({ title, description, due_date }),
    markAsComplete: (id) => Task.update({ status: 'complete' }, { where: { id } }),
    getAllTasks: (status) => Task.findAll({ where: { status } }),
    deleteTask: (id) => Task.destroy({ where: { id } })
};

module.exports = taskService;