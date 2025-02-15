import { React, useState } from "react";
import SendIcon from '@mui/icons-material/Send';
import CustomButton from "../common/button/CustomButton";

const ChatInterface = ({ selectedProject, ...props }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");

    const sendMessage = () => {
        if (input.trim()) {
        setMessages([...messages, { text: input, sender: "user" }]);
        setInput("");
        }
    };

    return (
        <div className="chat-section">
        <h2>{selectedProject}</h2>
        <div className="chat-messages">
            {messages.map((msg, index) => (
            <div key={index} className="message">
                <strong>{msg.sender}:</strong> {msg.text}
            </div>
            ))}
        </div>
        <div className="input-container">
            <input
            type="text"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            />
            <CustomButton version='bv1' variant='contained' onClick={sendMessage} endIcon={<SendIcon />}>Send</CustomButton>
        </div>
        </div>
    );
}

export default ChatInterface;