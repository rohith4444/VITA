import React, { useEffect, useRef, useState } from "react";
import "./chat.css";
import SendIcon from '@mui/icons-material/Send';
import MenuIcon from '@mui/icons-material/Menu';
import TextInput from "../common/textinput/TextInput";
import { InputAdornment } from "@mui/material";

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sidebarVisible, setSidebarVisible] = useState(true);

  const lastMessageRef = useRef(null);

  useEffect(() => {
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
    }
  }, [messages]);

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
      <div className="chat-container">
        <div className="chat">
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} ref={index === messages.length - 1 ? lastMessageRef : null}
                className={`message ${msg.sender === "user" ? "sent" : "received"}`}>
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
    </>
  );
};

export default ChatInterface;