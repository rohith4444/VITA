import React, { useEffect, useRef, useState } from "react";
import "./chat.css";
import { BookmarkBorder, Menu } from '@mui/icons-material';
import MessageBar from "../../../common/message_bar/MessageBar";
import { Switch } from "@mui/material";
import CodeEditor from "../codeeditor/CodeEditor";
import RightSidebar from "../right-sidebar/RightSidebar";

const label = { inputProps: { 'aria-label': 'Size switch demo' } };

const Chat = ({ rightSidebarOpen, setRightSidebarOpen }) => {

    const [leftWidth, setLeftWidth] = useState(50); // Initial width percentage
    const isResizing = useRef(false);
    const parentRef = useRef(null);
    const chatRef = useRef(null);

    const startResizing = (event) => {
        console.log(isResizing);
        isResizing.current = true;
        document.addEventListener("mousemove", resizeDivs);
        document.addEventListener("mouseup", stopResizing);
    };

    const resizeDivs = (event) => {
        if (!isResizing.current) return;
        console.log("widths: ", event.clientX, window.innerWidth, event.clientX/window.innerWidth);
        // const newWidth = (event.clientX / window.innerWidth) * 100;
        // console.log("new width: ", newWidth);
        if (parentRef.current && chatRef.current) {
            const parentWidth = parentRef.current.offsetWidth;
            const childWidth = chatRef.current.offsetWidth;
            const sideBarWidth = window.innerWidth - parentWidth;
            const relXPosition = event.clientX - sideBarWidth;
            const newWidth = ((parentWidth - relXPosition) / parentWidth) * 100;
            console.log("div widths: ", parentWidth, childWidth, sideBarWidth, relXPosition, newWidth)
            requestAnimationFrame(() => setLeftWidth(newWidth));
        }
        // if (newWidth > 10 && newWidth < 90) { // Prevent shrinking too much
            // setLeftWidth(newWidth);
            // clearTimeout(resizeTimeout.current)
            // resizeTimeout.current = setTimeout(() => {
            //     requestAnimationFrame(() => setLeftWidth(newWidth));
            // }, 50);
        // }
    };

    const stopResizing = () => {
        isResizing.current = false;
        document.removeEventListener("mousemove", resizeDivs);
        document.removeEventListener("mouseup", stopResizing);
    };

    const fileInputRef = useRef();
    const [attachedFiles, setAttachedFiles] = useState([]);
    const [messages, setMessages] = useState([]);
    const [isEditorOpen, setIsEditorOpen] = useState(false);

    const lastMessageRef = useRef(null);

    useEffect(() => {
        if (lastMessageRef.current) {
            lastMessageRef.current.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
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
        var recievedMsg = { sender: "llm", text: "This is a llm generated message and this is a very long message to see how the long messages generally work on this screen" };
        setMessages([...messages, msg, recievedMsg]);
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
                        <Menu className="save-icon" onClick={() => setRightSidebarOpen(!rightSidebarOpen)} />
                        <Switch {...label} checked={isEditorOpen} onClick={() => { setIsEditorOpen(!isEditorOpen) }} size="small" />
                    </div>
                    {/* </div> */}
                </div>
                <div className="chat-editor-container" ref={parentRef}>
                    <div ref={chatRef} className={`chat-messages-container ${isEditorOpen ? `messages-editor-open` : `messages-editor-close`} ${rightSidebarOpen ? "paddingless" : "paddingmore"}`}  style={{ width: `${leftWidth}%` }}>
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
                    {/* {isEditorOpen && <div className="divider" onMouseDown={startResizing}></div>} */}
                    {isEditorOpen && <div className="code-editor" style={{ width: `${100 - leftWidth}%` }}>
                        <CodeEditor />
                    </div>}
                    <RightSidebar open={rightSidebarOpen} setOpen={setRightSidebarOpen} />
                </div>
            </div>
        </>
    );
}

export default Chat;