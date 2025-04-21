import React, { useContext } from 'react';
import { TasksContext } from '../context/TasksContext';
import TaskItem from './TaskItem';

function TaskList() {
  const { tasks } = useContext(TasksContext);
  return tasks.map(task => <TaskItem key={task.id} task={task} />);
}

export default TaskList;