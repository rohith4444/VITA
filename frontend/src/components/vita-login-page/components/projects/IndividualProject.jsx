import React, { useEffect, useRef, useState } from "react";
import "./individualproject.css"
import MessageBar from "../../../common/message_bar/MessageBar";
import { ArrowBack, Menu } from '@mui/icons-material';

const IndividualProject = ({ setStateAllProjects, setStateChat }) => {
    const [attachedFiles, setAttachedFiles] = useState([]);
    const [messages, setMessages] = useState([]);
    const chatBoxRef = useRef(null);
    const fileInputRef = useRef();
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
    const onFileUpload = () => { }
    return (
        <>
            <div className="individual-project-container">
                <div className="individual-project-header">
                    <div className="individual-project-back" onClick={setStateAllProjects}>
                        <ArrowBack /> All projects
                    </div>
                    <div className="individual-project-menu">
                        <Menu />
                    </div>
                </div>
                <div className="individual-project-body">
                    <div className="individual-prject-description">
                        <h1 className="individual-project-name">Project Name</h1>
                        <p className="individual-project-name">Project Description</p>
                    </div>
                    <MessageBar
                        attachedFiles={attachedFiles}
                        onFileChange={onFileChange}
                        fileInputRef={fileInputRef}
                        deleteFile={deleteFile}
                        onSendMessage={sendMessage}
                    />
                    <div className="individual-project-recent-chats-container">
                        <div className="individual-project-recent-chats-header">
                            <h2 className="individual-project-recent-chats-title">💬 Your recent chats</h2>
                            <a href="#" className="last">view all</a>
                        </div>
                        <div className="individual-project-recent-chats-grid">
                            {Array.from({ length: 10 }).map((_, index) => (
                                <div className="individual-project-recent-chats-card" key={index} onClick={setStateChat}>
                                    <h3 className="individual-project-recent-card-heading">Project Structure for AI Agents and Tools</h3>
                                    <p className="individual-project-recent-card-time">4 hours ago</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default IndividualProject;