import React from 'react';
import Header from './Header';
import TaskList from './TaskList';
import TaskForm from './TaskForm';
import TaskFilter from './TaskFilter';

function App() {
  return (
    <div className='App'>
      <Header />
      <TaskFilter />
      <TaskList />
      <TaskForm />
    </div>
  );
}

export default App;