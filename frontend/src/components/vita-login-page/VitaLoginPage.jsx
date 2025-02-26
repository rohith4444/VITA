import React, { useEffect, useRef, useState } from "react";
import './vitaloginpage.css';
import Main from "./components/main/Main";
import { FolderOutlined, BookmarkBorderOutlined, KeyboardArrowLeft, KeyboardArrowRight, AddCircleOutline, Schedule, ChatOutlined } from '@mui/icons-material';
import Project from "./components/projects/Project";
import ChatInterface from "../chat-interface/ChatInterface";
import AllChats from "./components/allchats/AllChats";
import Chat from "./components/chat/Chat";
import IndividualProject from "./components/projects/IndividualProject";

const STATES = {
    MAIN: 'main',
    ALL_PROJECTS: 'all_projects',
    PROJECT: 'project',
    RECENT: 'recent',
    ALL_CHATS: 'all_chats',
    CHAT: 'chat'
};

const VitaLoginPage = () => {
    const [sidebarExpanded, setSidebarExpanded] = useState(true);
    const [state, setState] = useState(STATES.MAIN);
    const [projectsHovered, setProjectsHovered] = useState(false);
    const [chatsHovered, setChatsHovered] = useState(false);
    const [isRecentChats, setIsRecentChats] = useState(false);
    const [messages, setMessages] = useState([]);

    const lastMessageRef = useRef(null);
    const chatBoxRef = useRef(null);

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

    return (
        <>
            <div className="chatbot-container">
                <div className={`sidebar ${sidebarExpanded ? "expanded" : "collapsed"}`}>
                    <div className="sidebar-header">
                        <h2 className="sidebar-heading">
                            {sidebarExpanded ? "VITA" : "V"}
                        </h2>
                        <button className="menu-button" onClick={() => setSidebarExpanded(!sidebarExpanded)}>
                            {sidebarExpanded ? <KeyboardArrowLeft /> : <KeyboardArrowRight />}
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
                            <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-1</a>
                            <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-2</a>
                            <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-3</a>
                            <a href="#" className="last" onClick={() => { setState(STATES.ALL_CHATS); setIsRecentChats(false); }}>view all</a>
                        </div>}
                        <div className="sidebar-navItem">
                            <div className="sidebar-navitem-icon-text">
                                <Schedule />
                                {sidebarExpanded && "Recent Chats"}
                            </div>
                        </div>
                        {sidebarExpanded && <div className="sidebar-project-list">
                            <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-1</a>
                            <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-2</a>
                            <a href="#" className="sidebar-project-item" onClick={() => setState(STATES.CHAT)}>Chat-3</a>
                            <a href="#" className="last" onClick={() => { setState(STATES.ALL_CHATS); setIsRecentChats(true); }}>view all</a>
                        </div>}
                    </nav>
                    <div className="sidebar-profile-section">
                        <div className="sidebar-profile-icon">FL</div>
                        {sidebarExpanded && <div className="sidebar-profile-name">Firstname Lastname</div>}
                    </div>
                </div>
                <div className="chatbox" ref={chatBoxRef}>
                    {state === STATES.MAIN && <Main />}
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
                    {state === STATES.CHAT && <Chat />}
                    {state === STATES.ALL_CHATS && <AllChats isRecentChats={isRecentChats} />}
                </div>
            </div>
        </>
    );
}

export default VitaLoginPage;
