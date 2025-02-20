import React, { useEffect, useRef, useState } from "react";
import "./chat.css";
import SendIcon from '@mui/icons-material/Send';
import TextInput from "../common/textinput/TextInput";

const ChatInterface = ({ ...props }) => {
  // const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  // const lastMessageRef = useRef(null);

  // useEffect(() => {
  //   if (lastMessageRef.current) {
  //     lastMessageRef.current.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
  //   }
  // }, [messages]);

  const sendMessage = () => {
      props.sendMessage(input);
      setInput("");
  };

  return (
    <div className="chat-container">
      <div className="chat">
        <div className="chat-messages">
          {props.messages.map((msg, index) => (
            <div key={index} ref={index === props.messages.length - 1 ? props.lastMessageRef : null}
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
  );
};

export default ChatInterface;