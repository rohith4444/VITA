import React, { useState } from "react";
import "./messagebar.css";
import TextInput from "../textinput/TextInput";
import { AttachFileOutlined, Send, DeleteOutline } from '@mui/icons-material';

const MessageBar = ({ attachedFiles, onFileChange, fileInputRef, deleteFile, onSendMessage, ...props }) => {

    const [text, setText] = useState("");

    const renderAttachedFilePreview = () => {
        attachedFiles.forEach(e => console.log(e.name))
        return <div className="main-container-input-container-files">
            {attachedFiles.map((file, index) => (
                <div className="input-file-name" key={index}>
                    <div>{file.name.length > 30 ? `${file.name.substring(0, 30)}...` : file.name}</div>
                    <DeleteOutline className="input-file-name-close-button" onClick={(event) => { event.stopPropagation(); deleteFile(file.name) }} />
                </div>
            ))}
        </div>;
    };

    const sendMessage = (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            if (text !== "" && text !== "\n") {
                event.preventDefault()
                setText("");
                onSendMessage(text);
            }
        }
    }

    return (
        <>
            <div className="main-container-input-container">
                {attachedFiles.length > 0 && renderAttachedFilePreview()}
                <TextInput
                    variant="standard"
                    type="text"
                    placeholder="How can Claude help you today?"
                    className="main-container-input-text"
                    size="small"
                    InputProps={{
                        disableUnderline: true,
                    }}
                    multiline
                    maxRows={5}
                    value={text}
                    onChange={(event) => {setText(event.target.value)}}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage(e)}
                />
                <div className="min-container-input-meta">
                    <div className="min-container-input-meta-choose">
                    <div>
                        <a href="#" className="min-container-input-meta-choose-item">Claude 3.5 Sonnet ▾</a>
                    </div>
                    |
                    <div>
                        <a href="#" className="min-container-input-meta-choose-item">Choose agent ▾</a>
                    </div>
                    </div>
                    <div className="min-container-input-meta-send-message">
                    <input type="file" onChange={onFileChange} multiple ref={fileInputRef} hidden />
                    <AttachFileOutlined onClick={() => fileInputRef.current.click()} />
                    <Send sx={{ transform: "rotate(-90deg)" }} onClick={sendMessage}/>
                    </div>
                </div>
            </div>
        </>
    );
}

export default MessageBar;