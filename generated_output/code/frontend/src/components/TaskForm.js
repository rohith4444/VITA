import React, { useState, useContext } from 'react';
import { TaskContext } from '../context/TaskContext';

function TaskForm() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const { addTask } = useContext(TaskContext);

  const handleSubmit = (e) => {
    e.preventDefault();
    addTask(title, description, dueDate);
    setTitle('');
    setDescription('');
    setDueDate('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type='text' value={title} onChange={(e) => setTitle(e.target.value)} placeholder='Title' required />
      <input type='text' value={description} onChange={(e) => setDescription(e.target.value)} placeholder='Description' required />
      <input type='date' value={dueDate} onChange={(e) => setDueDate(e.target.value)} required />
      <button type='submit'>Add Task</button>
    </form>
  );
}

export default TaskForm;