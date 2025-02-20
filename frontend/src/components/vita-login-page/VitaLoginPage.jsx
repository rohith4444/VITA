import React, { useState } from "react";
import './vitaloginpage.css';
import MenuIcon from '@mui/icons-material/Menu';
import Header from "../common/header/Header";
import Footer from "../common/footer/Footer";
import Main from "./components/main/Main";
import { Home, Sms, Bookmark, Settings, AccountTree, KeyboardArrowUp, KeyboardArrowDown, AddCircleOutline, Schedule } from '@mui/icons-material';
import Project from "./components/projects/Project";
import ChatInterface from "../chat-interface/ChatInterface";

const styles = {
    nav: {
      display: "flex",
      flexDirection: "column",
      gap: "15px",
    },
    navItem: {
      color: "black",
      textDecoration: "none",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      fontSize: "16px",
      padding: "5px",
      borderRadius: "8px",
      transition: "background 0.2s",
    },
    navItemHover: {
      backgroundColor: "#2c2f33",
    },
    profileSection: {
      marginTop: "auto",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      padding: "10px",
      borderTop: "1px solid #444",
    },
    profileIcon: {
      width: "40px",
      height: "40px",
      backgroundColor: "#444",
      borderRadius: "50%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: "18px",
    },
    profileName: {
      fontSize: "16px",
    },
    projectList: {
        display: "flex",
        flexDirection: "column",
        paddingLeft: "30px",
        gap: "10px",
    },
    projectItem: {
        color: "black",
        textDecoration: "none",
        fontSize: "14px",
        padding: "0px 0",
        textAlign: "left"
    },
};

const STATES = {
    MAIN: 'main',
    PROJECT: 'project',
    RECENT: 'recent'
}

const VitaLoginPage = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sidebarVisible, setSidebarVisible] = useState(true);
    const [isProjectsExpanded, setIsProjectsExpanded] = useState(false);
    const [state, setState] = useState(STATES.MAIN);
    const [newProject, setNewProject] = useState(false);

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
                    <div className="options-container">
                        <nav style={styles.nav}>
                            <div style={styles.navItem} onClick={() => {setNewProject(false);setState(STATES.PROJECT)}}>
                                <AccountTree /> 
                                Projects 
                                {isProjectsExpanded ? <KeyboardArrowUp onClick={() => setIsProjectsExpanded(!isProjectsExpanded)} /> : <KeyboardArrowDown onClick={() => setIsProjectsExpanded(!isProjectsExpanded)} />}
                                <AddCircleOutline onClick={(event) => {event.stopPropagation();setNewProject(true);setState(STATES.PROJECT)}}/>
                            </div>
                            {isProjectsExpanded && (
                            <div style={styles.projectList}>
                                <a href="#" style={styles.projectItem}> Project-1</a>
                                <a href="#" style={styles.projectItem}> Project-2</a>
                                <a href="#" style={styles.projectItem}> Project-3</a>
                            </div>
                            )}
                            {/* <a href="#" style={styles.navItem}><Bookmark /> Saved</a>
                            <a href="#" style={styles.navItem}><Settings /> Settings</a> */}
                            <a href="#" onClick={() => setState(STATES.RECENT)} style={styles.navItem}><Schedule /> Recent Chats</a>
                        </nav>
                        <div style={styles.profileSection}>
                            <div style={styles.profileIcon}>M</div>
                            <div style={styles.profileName}>Username</div>
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
                    {STATES.RECENT == state && <ChatInterface />}
                </div>
            </div>
            <Footer />
        </>
    );
}

export default VitaLoginPage;