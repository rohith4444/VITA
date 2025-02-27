import React, { createContext, useState } from 'react';

export const TaskContext = createContext();

export const TaskProvider = props => {
  const [tasks, setTasks] = useState([]);
  const addTask = (title, description) => {
    setTasks([...tasks, { id: Date.now(), title, description }]);
  };
  const deleteTask = id => {
    setTasks(tasks.filter(task => task.id !== id));
  };
  return (
    <TaskContext.Provider value={{ tasks, addTask, deleteTask }}>
      {props.children}
    </TaskContext.Provider>
  );
};