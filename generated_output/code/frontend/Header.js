import React from 'react';
import { Link } from 'react-router-dom';

function Header() {
  return (
    <header>
      <h1>Todo List</h1>
      <nav>
        <Link to='/'>Home</Link>
        <Link to='/add'>Add Task</Link>
      </nav>
    </header>
  );
}

export default Header;