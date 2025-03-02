import React, { useContext } from 'react';
import TaskItem from './TaskItem';
import { TaskContext } from '../context/TaskContext';

function TaskList() {
  const { tasks } = useContext(TaskContext);
  return tasks.map(task => <TaskItem key={task.id} task={task} />);
}

export default TaskList;