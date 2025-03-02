import React from 'react';

function TaskItem({ task }) {
  return (
    <div>
      <h2>{task.title}</h2>
      <p>{task.description}</p>
      <p>{task.dueDate}</p>
      <button onClick={() => completeTask(task.id)}>Complete</button>
      <button onClick={() => deleteTask(task.id)}>Delete</button>
    </div>
  );
}

export default TaskItem;