import React, { useContext } from 'react';
import { TaskContext } from '../context/TaskContext';
import TaskItem from './TaskItem';

const TaskList = () => {
  const { tasks } = useContext(TaskContext);
  return tasks.map(task => <TaskItem key={task.id} task={task} />);
};

export default TaskList;