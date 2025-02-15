import React, { useState } from 'react';
import './chat.css';
import Sidebar from './Sidebar';
import ChatInterface from './ChatInterface';

const Chat = () => {
    const [selectedProject, setSelectedProject] = useState("Chat Interface Design");

  return (
    <div className="chat-container">
      <Sidebar onSelectProject={setSelectedProject} />
      <ChatInterface selectedProject={selectedProject} />
    </div>
  );
}

export default Chat;