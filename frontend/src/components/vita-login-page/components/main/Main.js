import React, { useRef, useState } from "react";
import './main.css';
import MessageBar from "../../../common/message_bar/MessageBar";
import { DeleteOutline } from '@mui/icons-material';

const Main = (props) => {
  const { setStateProject, onStartNewChat, onFileChange, deleteFile, onFileUpload, attachedFiles, fileInputRef } = props;
  return (
    <div className="main-container">
      <div className="main-container-content-wrapper">
        <div className="main-container-header">
          <h1 className="main-container-header-h1">Welcome, Firstname</h1>
          {/* <span style={styles.planBadge}>Professional Plan</span> */}
        </div>
        
        <MessageBar
          attachedFiles={attachedFiles}
          onFileChange={onFileChange}
          fileInputRef={fileInputRef}
          deleteFile={deleteFile}
          onSendMessage={onStartNewChat}
        />
        
        <div className="main-container-recent-chats-container">
          <div className="main-container-recent-chats-header">
            <h2 className="main-container-recent-chats-title">💬 Your recent chats</h2>
            <a href="#" className="last">view all</a>
          </div>
          <div className="main-container-recent-chats-grid">
            {Array.from({ length: 5 }).map((_, index) => (
              <div className="main-container-recent-chats-card card" key={index} onClick={setStateProject}>
                <h3 className="main-container-recent-card-heading">Project Structure for AI Agents and Tools</h3>
                <p className="main-container-recent-card-time">4 hours ago</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Main;
