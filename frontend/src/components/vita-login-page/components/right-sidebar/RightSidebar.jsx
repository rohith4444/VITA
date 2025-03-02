import React, { useState } from "react";
import "./rightsidebar.css";
import { ClearRounded, ArrowDropDownRounded, KeyboardArrowDownRounded, KeyboardArrowUpRounded } from '@mui/icons-material';
import CustomButton from "../../../common/button/CustomButton";

const RightSidebar = ({ open, setOpen }) => {
    const [dropdownOpen, setDropdownOpen] = useState(false);
    return (
        <div className={`rightsidebar ${open ? "visible" : "not-visible"}`}>
            <div className="rightsidebar-header">
                <ClearRounded onClick={() => setOpen(!open)} />
                <h2>Files</h2>
            </div>
            <div className="rightsidebar-items">
                <div className="sidebar-navItem" onClick={() => setDropdownOpen(!dropdownOpen)}>
                    <div className="sidebar-navitem-icon-text fontsize-large">
                        Your files
                        {dropdownOpen ? <KeyboardArrowUpRounded /> : <KeyboardArrowDownRounded />}
                    </div>
                    <CustomButton onClick={(event) => {event.stopPropagation();}}>Upload Files</CustomButton>
                </div>
                {dropdownOpen && <div className="sidebar-project-list">
                    <a href="#" className="sidebar-project-item">Chat-1</a>
                    <a href="#" className="sidebar-project-item">Chat-2</a>
                    <a href="#" className="sidebar-project-item">Chat-3</a>
                </div>}
            </div>
        </div>
    );
}

export default RightSidebar;