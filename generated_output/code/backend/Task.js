const Sequelize = require('sequelize');
const db = require('../db');

const Task = db.define('task', {
  title: Sequelize.STRING,
  description: Sequelize.STRING,
  due_date: Sequelize.DATE,
  completed: { type: Sequelize.BOOLEAN, defaultValue: false }
});

module.exports = Task;