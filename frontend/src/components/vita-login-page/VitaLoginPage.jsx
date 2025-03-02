import React, { useEffect, useRef, useState } from "react";
import './vitaloginpage.css';
import Main from "./components/main/Main";
import { ArrowForwardRounded, FolderOutlined, BookmarkBorderOutlined, KeyboardDoubleArrowLeftRounded, KeyboardDoubleArrowRightRounded, AddCircleOutline, Schedule, ChatOutlined } from '@mui/icons-material';
import Project from "./components/projects/Project";
import ChatInterface from "../chat-interface/ChatInterface";
import AllChats from "./components/allchats/AllChats";
import Chat from "./components/chat/Chat";
import IndividualProject from "./components/projects/IndividualProject";
import { useNavigate } from "react-router-dom";

const STATES = {
    MAIN: 'main',
    ALL_PROJECTS: 'all_projects',
    PROJECT: 'project',
    RECENT: 'recent',
    ALL_CHATS: 'all_chats',
    CHAT: 'chat'
};

const VitaLoginPage = ({ defaultState, defaultChatId, defaultProjectId, ...props }) => {
    if (!defaultState) {
        defaultState = STATES.MAIN
    }

    const firstName = "Firstname"
    const lastName = "Lastname"

    const [chatId, setChatId] = useState(defaultChatId);
    const [projectId, setProjectId] = useState(defaultProjectId);
    const [sidebarExpanded, setSidebarExpanded] = useState(true);
    const [state, setState] = useState(defaultState);
    const [projectsHovered, setProjectsHovered] = useState(false);
    const [chatsHovered, setChatsHovered] = useState(false);
    const [isRecentChats, setIsRecentChats] = useState(false);
    const [messages, setMessages] = useState([]);
    const [rightSidebarOpen, setRightSidebarOpen] = useState(false);
    const [attachedFiles, setAttachedFiles] = useState([]);
    const fileInputRef = useRef();
    const lastMessageRef = useRef(null);
    const chatBoxRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        if (chatBoxRef.current) {
            chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
        }
    }, [messages]);

    const handleMouseEnterProjects = () => {
        setProjectsHovered(true);
    };

    const handleMouseLeaveProjects = () => {
        setProjectsHovered(false);
    };

    const handleMouseEnterChats = () => {
        setChatsHovered(true);
    };

    const handleMouseLeaveChats = () => {
        setChatsHovered(false);
    };

    const onStartNewChat = (message) => {
        setState(STATES.CHAT);
        var msg = { sender: "user", text: message };
        var recievedMsg = { sender: "llm", text: "This is a llm generated message and this is a very long message to see how the long messages generally work on this screen" };
        setMessages([msg, recievedMsg]);
    }

    const updateMessages = (message) => {
        var msg = { sender: "user", text: message };
        var recievedMsg = { sender: "llm", text: "This is a llm generated message and this is a very long message to see how the long messages generally work on this screen" };
        setMessages([...messages, msg, recievedMsg]);
    }

    const onFileChange = (event) => {
        if (event.target.files) {
            setAttachedFiles([...attachedFiles, event.target.files[0]]);
        }
    };

    const deleteFile = (fileName) => {
        setAttachedFiles((prevFiles) => prevFiles.filter(file => file.name !== fileName));
    }

    // On file upload (click the upload button)
    const onFileUpload = () => {
    };

    return (
        <>
            <div className="chatbot-container">
                <div className={`sidebar ${sidebarExpanded ? "expanded" : "collapsed"}`}>
                    <div className="sidebar-header">
                        <h2 className="sidebar-heading">
                            {sidebarExpanded ? "VITA" : "V"}
                        </h2>
                        <button className="menu-button" onClick={() => setSidebarExpanded(!sidebarExpanded)}>
                            {sidebarExpanded ? <KeyboardDoubleArrowLeftRounded fontSize="large" /> : <KeyboardDoubleArrowRightRounded fontSize="large" />}
                        </button>
                    </div>
                    <nav className="sidebar-nav">
                        <div className="sidebar-navItem" onClick={() => setState(STATES.MAIN)} onMouseEnter={handleMouseEnterChats} onMouseLeave={handleMouseLeaveChats}>
                            <div className="sidebar-navitem-icon-text">
                                <ChatOutlined />
                                {sidebarExpanded && "New Chat"}
                            </div>
                            {chatsHovered && <AddCircleOutline />}
                        </div>
                        <div className="sidebar-navItem" onClick={() => setState(STATES.ALL_PROJECTS)} onMouseEnter={handleMouseEnterProjects} onMouseLeave={handleMouseLeaveProjects}>
                            <div className="sidebar-navitem-icon-text">
                                <FolderOutlined />
                                {sidebarExpanded && "Projects"}
                            </div>
                            {projectsHovered && <AddCircleOutline />}
                        </div>
                        <div className="sidebar-navItem">
                            <div className="sidebar-navitem-icon-text">
                                <BookmarkBorderOutlined />
                                {sidebarExpanded && "Favorites"}
                            </div>
                        </div>
                        {sidebarExpanded && <div className="sidebar-project-list">
                            {
                                [...Array(5)].map((_, i) => {
                                    return <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-{i+1}</a>
                                })
                            }
                            <a href="#" className="last" onClick={() => {setState(STATES.ALL_CHATS);setIsRecentChats(false);}}>
                                view all<ArrowForwardRounded fontSize="small" />
                            </a>
                        </div>}
                        <div className="sidebar-navItem">
                            <div className="sidebar-navitem-icon-text">
                                <Schedule />
                                {sidebarExpanded && "Recent Chats"}
                            </div>
                        </div>
                        {sidebarExpanded && <div className="sidebar-project-list">
                            {
                                [...Array(5)].map((_, i) => {
                                    return <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-{i+1}</a>
                                })
                            }
                            <a href="#" className="last" onClick={() => {setState(STATES.ALL_CHATS);setIsRecentChats(true);}}>
                                view all<ArrowForwardRounded fontSize="small" />
                            </a>
                        </div>}
                    </nav>
                    <div className="sidebar-profile-section">
                        <div className="sidebar-profile-icon">{firstName[0]}{lastName[0]}</div>
                        {sidebarExpanded && <div className="sidebar-profile-name">{firstName} {lastName}</div>}
                    </div>
                </div>
                <div className="chatbox" ref={chatBoxRef}>
                    {state === STATES.MAIN && 
                        <Main 
                            setStateProject={() => setState(STATES.PROJECT)} 
                            messages={messages} 
                            lastMessageRef={lastMessageRef} 
                            onStartNewChat={onStartNewChat}
                            updateMessages={updateMessages}
                            attachedFiles={attachedFiles}
                            onFileChange={onFileChange}
                            deleteFile={deleteFile}
                            onFileUpload={onFileUpload}
                            fileInputRef={fileInputRef}
                        />
                    }
                    {state === STATES.PROJECT &&
                        <IndividualProject
                            setStateAllProjects={() => setState(STATES.ALL_PROJECTS)}
                            setStateChat={() => setState(STATES.CHAT)}
                        />
                    }
                    {state === STATES.ALL_PROJECTS &&
                        <Project setStateProject={() => setState(STATES.PROJECT)} />
                    }
                    {state === STATES.RECENT &&
                        <ChatInterface messages={messages} lastMessageRef={lastMessageRef} />
                    }
                    {state === STATES.CHAT && 
                        <Chat 
                            rightSidebarOpen={rightSidebarOpen} 
                            setRightSidebarOpen={setRightSidebarOpen} 
                            messages={messages}
                            updateMessages={updateMessages}
                            attachedFiles={attachedFiles}
                            onFileChange={onFileChange}
                            deleteFile={deleteFile}
                            onFileUpload={onFileUpload}
                            fileInputRef={fileInputRef}
                            lastMessageRef={lastMessageRef}
                        />
                    }
                    {state === STATES.ALL_CHATS && <AllChats isRecentChats={isRecentChats} />}
                </div>
            </div>
        </>
    );
}

export default VitaLoginPage;
