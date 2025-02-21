import React from "react";
import { Lightbulb, StickyNote2, Summarize } from '@mui/icons-material';
import './main.css';
import CustomButton from "../../../common/button/CustomButton";
import TextInput from "../../../common/textinput/TextInput";

const Main = () => {
  return (
    <div className="main-container">
      <div className="main-container-content-wrapper">
        <div className="main-container-header">
          <h1 className="main-container-header-h1">Good afternoon</h1>
          {/* <span style={styles.planBadge}>Professional Plan</span> */}
        </div>
        
        <div className="main-container-input-container">
          <TextInput
            type="text"
            placeholder="How can Claude help you today?"
            className="main-container-input-text"
            size="small"
          />
          <div className="main-container-input-meta">Claude 3.5 Sonnet ▾ | Choose style ▾</div>
          
          <div className="main-container-button-group">
            <CustomButton className="main-container-button-group-button" version="v2" padding="5px 10px">
              <Lightbulb />Generate interview questions
            </CustomButton>
            <CustomButton className="main-container-button-group-button" version="v2">
              <StickyNote2 fontSize="large" /> Write a memo
            </CustomButton>
            <CustomButton className="main-container-button-group-button" version="v2">
              <Summarize fontSize="large" /> Summarize meeting notes
            </CustomButton>
          </div>
        </div>
        
        <div className="main-container-recent-chats-container">
          <h2 className="main-container-recent-chats-title">💬 Your recent chats</h2>
          <div className="main-container-recent-chats-grid">
            {Array.from({ length: 3 }).map((_, index) => (
              <div className="main-container-recent-chats-card" key={index}>
                {/* <span className="main-container-recent-card-tag">AETHER AI</span> */}
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
