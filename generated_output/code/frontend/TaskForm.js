import React, { useState, useContext } from 'react';
import { TaskContext } from '../context/TaskContext';

const TaskForm = () => {
  const { addTask } = useContext(TaskContext);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const handleSubmit = e => {
    e.preventDefault();
    addTask(title, description);
    setTitle('');
    setDescription('');
  };
  return (
    <form onSubmit={handleSubmit}>
      <input type='text' value={title} onChange={e => setTitle(e.target.value)} placeholder='Title' required />
      <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder='Description' required />
      <button type='submit'>Add Task</button>
    </form>
  );
};

export default TaskForm;