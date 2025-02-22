import React, { useEffect, useRef, useState } from "react";
import './vitaloginpage.css';
import MenuIcon from '@mui/icons-material/Menu';
import Main from "./components/main/Main";
import { AccountTree, KeyboardArrowUp, KeyboardArrowDown, AddCircleOutline, Schedule, Home, SupportAgent } from '@mui/icons-material';
import Project from "./components/projects/Project";
import ChatInterface from "../chat-interface/ChatInterface";

const STATES = {
    MAIN: 'main',
    PROJECT: 'project',
    RECENT: 'recent'
}

const VitaLoginPage = () => {
    const [chatId, setChatId] = useState("");
    const [sidebarVisible, setSidebarVisible] = useState(true);
    const [isProjectsExpanded, setIsProjectsExpanded] = useState(false);
    const [isAgentsExpanded, setIsAgentsExpanded] = useState(false);
    const [state, setState] = useState(STATES.MAIN);
    const [newProject, setNewProject] = useState(false);

    const [messages, setMessages] = useState([]);
    const lastMessageRef = useRef(null);

    useEffect(() => {
        if (lastMessageRef.current) {
          lastMessageRef.current.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
        }
    }, [messages]);

    const getAllMessages = (chatId) => {
        if (chatId.trim()) {
            setMessages([{ text: chatId, sender: "user" }]);
            setTimeout(() => {
              setMessages((prevMessages) => [...prevMessages, { text: "This is a bot response", sender: "bot" }]);
            }, 1000);
          }
    }

    const sendMessage = (input) => {
        if (input.trim()) {
          setMessages((prevMessages) => [...prevMessages, { text: input, sender: "user" }]);
          setTimeout(() => {
            setMessages((prevMessages) => [...prevMessages, { text: "This is a bot response", sender: "bot" }]);
          }, 1000);
        }
    };

    return (
        <>
            {/* <Header /> */}
            <div className="chatbot-container">
                <div className={`sidebar ${sidebarVisible ? "visible" : ""}`}>
                    <button className="close-sidebar" onClick={() => setSidebarVisible(false)}>✖</button>
                    <div className="options-container">
                        <nav className="sidebar-nav">
                            <div className="sidebar-navItem">
                                <div className="sidebar-navitem-icon-text" onClick={() => {setState(STATES.MAIN)}}>
                                    <SupportAgent /> Agents
                                    {isAgentsExpanded ? 
                                        <KeyboardArrowUp onClick={(event) => {event.stopPropagation();setIsAgentsExpanded(!isAgentsExpanded)}} /> : 
                                        <KeyboardArrowDown onClick={(event) => {event.stopPropagation();setIsAgentsExpanded(!isAgentsExpanded)}} />
                                    }
                                </div>
                                <AddCircleOutline onClick={(event) => {event.stopPropagation();setNewProject(!newProject);setState(STATES.PROJECT)}}/>
                            </div>
                            {isAgentsExpanded && (
                                <div className="sidebar-project-list">
                                    <a href="#" className="sidebar-project-item"> Agent-1</a>
                                    <a href="#" className="sidebar-project-item"> Agent-2</a>
                                    <a href="#" className="sidebar-project-item"> Agent-3</a>
                                </div>
                            )}
                            <div className="sidebar-navItem" onClick={() => {setNewProject(false);setState(STATES.PROJECT)}}>
                                <div className="sidebar-navitem-icon-text">
                                    <AccountTree /> 
                                    Projects 
                                    {isProjectsExpanded ? 
                                        <KeyboardArrowUp onClick={(event) => {event.stopPropagation();setIsProjectsExpanded(!isProjectsExpanded)}} /> : 
                                        <KeyboardArrowDown onClick={(event) => {event.stopPropagation();setIsProjectsExpanded(!isProjectsExpanded)}} />
                                    }
                                </div>
                                <AddCircleOutline onClick={(event) => {event.stopPropagation();setNewProject(!newProject);setState(STATES.PROJECT)}}/>
                            </div>
                            {isProjectsExpanded && (
                                <div className="sidebar-project-list">
                                    <a href="#" className="sidebar-project-item"> Project-1</a>
                                    <a href="#" className="sidebar-project-item"> Project-2</a>
                                    <a href="#" className="sidebar-project-item"> Project-3</a>
                                </div>
                            )}
                            {/* <a href="#" style={styles.navItem}><Bookmark /> Saved</a>
                            <a href="#" style={styles.navItem}><Settings /> Settings</a> */}
                            <div className="sidebar-navItem margin-top-2rem">
                                <div className="sidebar-navitem-icon-text sidebar-navItem">
                                    <Schedule /> Recent Chats
                                </div>
                            </div>
                            <div className="sidebar-project-list">
                                <a className="sidebar-project-item"
                                    onClick={() => {setState(STATES.RECENT);getAllMessages("Project-1");setChatId("Project-1");}}>
                                    Project-1
                                </a>
                                <a className="sidebar-project-item"
                                    onClick={() => {setState(STATES.RECENT);getAllMessages("Project-2");setChatId("Project-2");}}>
                                    Project-2
                                </a>
                                <a className="sidebar-project-item"
                                    onClick={() => {setState(STATES.RECENT);getAllMessages("Project-3");setChatId("Project-3");}}>
                                    Project-3
                                </a>
                            </div>
                        </nav>
                        <div className="sidebar-profile-section">
                            <div className="sidebar-profile-icon">FL</div>
                            <div className="sidebar-profile-name">Firstname Lastname</div>
                        </div>
                    </div>
                </div>
                
                <div className="chatbox">
                    <div className="chat-header">
                        <button className="menu-button" onClick={() => setSidebarVisible(!sidebarVisible)}>
                            <MenuIcon size={24} />
                        </button>
                    </div>
                    {STATES.MAIN == state && <Main />}
                    {STATES.PROJECT == state && <Project newProject={newProject} />}
                    {/* {STATES.RECENT == state && <></>} */}
                    {STATES.RECENT == state && 
                    <ChatInterface messages={messages} lastMessageRef={lastMessageRef} chatId={chatId} sendMessage={sendMessage} />}
                </div>
            </div>
            {/* <Footer /> */}
        </>
    );
}

export default VitaLoginPage;