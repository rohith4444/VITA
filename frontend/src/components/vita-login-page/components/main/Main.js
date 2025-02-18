import React from "react";
import { Lightbulb, StickyNote2, Summarize } from '@mui/icons-material';
import './main.css';
import CustomButton from "../../../common/button/CustomButton";

const styles = {
  container: {
    minHeight: "100%",
    padding: "32px",
  },
  contentWrapper: {
    // maxWidth: "900px",
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#333",
  },
  planBadge: {
    backgroundColor: "#e0c3fc",
    color: "#6a0dad",
    padding: "5px 10px",
    borderRadius: "16px",
    fontSize: "12px",
  },
  inputContainer: {
    marginTop: "24px",
    padding: "24px",
    backgroundColor: "#fff",
    boxShadow: "0px 4px 6px rgba(0,0,0,0.1)",
    borderRadius: "12px",
  },
  inputField: {
    width: "100%",
    fontSize: "16px",
    padding: "12px",
    border: "1px solid #ccc",
    borderRadius: "8px",
    outline: "none",
  },
  inputMeta: {
    marginTop: "12px",
    color: "#666",
  },
  buttonGroup: {
    marginTop: "16px",
    display: "flex",
    gap: "8px",
  },
  button: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    backgroundColor: "#ddd",
    padding: "10px 16px",
    borderRadius: "8px",
    color: "#333",
    cursor: "pointer",
  },
  recentChatsContainer: {
    marginTop: "32px",
  },
  recentChatsTitle: {
    fontSize: "18px",
    fontWeight: "bold",
    color: "#555",
  },
  chatGrid: {
    marginTop: "16px",
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
    gap: "12px",
  },
  chatCard: {
    padding: "16px",
    backgroundColor: "#fff",
    boxShadow: "0px 4px 6px rgba(0,0,0,0.1)",
    borderRadius: "8px",
  },
  chatTag: {
    fontSize: "10px",
    backgroundColor: "#ccc",
    padding: "4px 8px",
    borderRadius: "12px",
  },
  chatTitle: {
    fontSize: "14px",
    fontWeight: "bold",
    marginTop: "8px",
  },
  chatTime: {
    fontSize: "12px",
    color: "#777",
    marginTop: "4px",
  },
};

const Main = () => {
  return (
    <div className="main-container">
      <div className="main-container-content-wrapper">
        <div className="main-container-header">
          <h1 className="main-container-header-h1">Good afternoon</h1>
          {/* <span style={styles.planBadge}>Professional Plan</span> */}
        </div>
        
        <div className="main-container-input-container">
          <input
            type="text"
            placeholder="How can Claude help you today?"
            className="main-container-input-text"
          />
          <div className="main-container-input-meta">Claude 3.5 Sonnet ▾ | Choose style ▾</div>
          
          <div className="main-container-button-group">
            <CustomButton className="main-container-button-group-button" version="v2"><Lightbulb fontSize="large" />Generate interview questions</CustomButton>
            <CustomButton className="main-container-button-group-button" version="v2"><StickyNote2 fontSize="large" /> Write a memo</CustomButton>
            <CustomButton className="main-container-button-group-button" version="v2"><Summarize fontSize="large" /> Summarize meeting notes</CustomButton>
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
