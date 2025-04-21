import React from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import Header from './components/Header';
import TaskList from './components/TaskList';
import TaskForm from './components/TaskForm';
import TasksContextProvider from './context/TasksContext';

function App() {
  return (
    <TasksContextProvider>
      <Router>
        <Header />
        <Route path='/' exact component={TaskList} />
        <Route path='/add' component={TaskForm} />
      </Router>
    </TasksContextProvider>
  );
}

export default App;