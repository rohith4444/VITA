import React, { useState } from "react";
import "./chat.css";
import SendIcon from '@mui/icons-material/Send';
import MenuIcon from '@mui/icons-material/Menu';
import TextInput from "../common/textinput/TextInput";
import { InputAdornment } from "@mui/material";
import Header from "../common/header/Header";
import Footer from "../common/footer/Footer";

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sidebarVisible, setSidebarVisible] = useState(true);

  const sendMessage = () => {
    if (input.trim()) {
      setMessages((prevMessages) => [...prevMessages, { text: input, sender: "user" }]);
      setTimeout(() => {
        setMessages((prevMessages) => [...prevMessages, { text: "This is a bot response", sender: "bot" }]);
      }, 1000);
      setInput("");
    }
  };

  return (
    <>
      <Header />
      <div className="chatbot-container">
        <div className={`sidebar ${sidebarVisible ? "visible" : ""}`}>
          <button className="close-sidebar" onClick={() => setSidebarVisible(false)}>✖</button>
        </div>
        
        <div className="chatbox">
          <div className="chat-header">
            <button className="menu-button" onClick={() => setSidebarVisible(!sidebarVisible)}>
              <MenuIcon size={24} />
            </button>
          </div>
          
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.sender === "user" ? "sent" : "received"}`}>
                {msg.text}
              </div>
            ))}
          </div>
          
          <div className="chat-input">
            <TextInput
              type="text" 
              // placeholder="Type a message..." 
              label="Message your Agent"
              value={input} 
              fullWidth
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button className="send-button" onClick={sendMessage}>
              <SendIcon size={20} />
            </button>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default Chat;