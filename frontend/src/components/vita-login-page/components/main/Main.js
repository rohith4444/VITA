import React, { useRef, useState } from "react";
import './main.css';
import MessageBar from "../../../common/message_bar/MessageBar";
import { DeleteOutline } from '@mui/icons-material';

const Main = () => {
  const fileInputRef = useRef();
  const [attachedFiles, setAttachedFiles] = useState([]);

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
        />
        
        <div className="main-container-recent-chats-container">
          <div className="main-container-recent-chats-header">
            <h2 className="main-container-recent-chats-title">💬 Your recent chats</h2>
            <a href="#" className="last">view all</a>
          </div>
          <div className="main-container-recent-chats-grid">
            {Array.from({ length: 3 }).map((_, index) => (
              <div className="main-container-recent-chats-card" key={index}>
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
