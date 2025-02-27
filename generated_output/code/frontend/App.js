import React from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import Header from './components/Header';
import TaskList from './components/TaskList';
import TaskForm from './components/TaskForm';
import { TaskProvider } from './context/TaskContext';

const App = () => {
  return (
    <TaskProvider>
      <Router>
        <Header />
        <Route path='/' exact component={TaskList} />
        <Route path='/add' component={TaskForm} />
      </Router>
    </TaskProvider>
  );
};

export default App;