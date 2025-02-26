import React, { useEffect, useRef, useState } from "react";
import "./chat.css";
import { BookmarkBorder, Menu } from '@mui/icons-material';
import MessageBar from "../../../common/message_bar/MessageBar";
import { Switch } from "@mui/material";

const label = { inputProps: { 'aria-label': 'Size switch demo' } };

const Chat = () => {
    const fileInputRef = useRef();
    const [attachedFiles, setAttachedFiles] = useState([]);
    const [messages, setMessages] = useState([]);
    const [isEditorOpen, setIsEditorOpen] = useState(true);

    const lastMessageRef = useRef(null);
    const chatBoxRef = useRef(null);

    useEffect(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [messages]);

    const onFileChange = (event) => {
        if (event.target.files) {
            setAttachedFiles([...attachedFiles, event.target.files[0]]);
        }
    };

    const deleteFile = (fileName) => {
        setAttachedFiles((prevFiles) => prevFiles.filter(file => file.name !== fileName));
    }

    const sendMessage = (message) => {
        var msg = { sender: "user", text: message };
        setMessages([...messages, msg]);
    }

    // On file upload (click the upload button)
    const onFileUpload = () => {
        // Create an object of formData
        // const formData = new FormData();

        // Update the formData object
        // formData.append(
        //     "myFile",
        //     this.state.selectedFile,
        //     this.state.selectedFile.name
        // );

        // Details of the uploaded file
        // console.log(this.state.selectedFile);

        // Request made to the backend api
        // Send formData object
        // axios.post("api/uploadfile", formData);
    };
    return (
        <>
            <div className="chat-container">
                <div className="chat-header">
                    {/* <div className="chat-heading"> */}
                    <h2 className="chat-heading-name">Chat Name</h2>
                    {/* </div>
                    <div className="chat-save"> */}
                    <div className="chat-heading-icons">
                        <BookmarkBorder className="save-icon" />
                        <Menu className="save-icon" />
                        <Switch {...label} checked={isEditorOpen} onClick={() => { setIsEditorOpen(!isEditorOpen) }} size="small" />
                    </div>
                    {/* </div> */}
                </div>
                <div className="chat-editor-container">
                    <div className={`chat-messages-container ${isEditorOpen ? `messages-editor-open` : `messages-editor-close`}`}>
                        <div className="chat-messages">
                            {messages.map((msg, index) => (
                                <div key={index} ref={index === messages.length - 1 ? lastMessageRef : null}
                                    className={`message ${msg.sender === "user" ? "sent" : "received"}`}>
                                    {msg.text}
                                </div>
                            ))}
                        </div>
                        <MessageBar
                            attachedFiles={attachedFiles}
                            onFileChange={onFileChange}
                            fileInputRef={fileInputRef}
                            deleteFile={deleteFile}
                            onSendMessage={sendMessage}
                        />
                    </div>
                    {isEditorOpen && <div className="code-editor">

                    </div>}
                </div>
            </div>
        </>
    );
}

export default Chat;