const Sequelize = require('sequelize');
const db = require('../db');

const Task = db.define('task', {
    title: { type: Sequelize.STRING, allowNull: false },
    description: { type: Sequelize.STRING },
    due_date: { type: Sequelize.DATE },
    status: { type: Sequelize.STRING, defaultValue: 'incomplete' }
});

module.exports = Task;