import React, { useContext } from 'react';
import { TasksContext } from '../context/TasksContext';

function TaskItem({ task }) {
  const { completeTask, deleteTask } = useContext(TasksContext);
  return (
    <div>
      <h2>{task.title}</h2>
      <p>{task.description}</p>
      <button onClick={() => completeTask(task.id)}>Complete</button>
      <button onClick={() => deleteTask(task.id)}>Delete</button>
    </div>
  );
}

export default TaskItem;