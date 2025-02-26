import React from "react";
import './gridlayout.css';
import CustomButton from "../button/CustomButton";

const GridLayout = ({ heading1, heading2, desc, btnVersion,  ...props }) => {
    if (btnVersion === null) {
        btnVersion = 'v1'
    }
    return (
        <div className="claude-card">
            <p className="claude-title">{heading1}</p>
            {heading2 ? <h2 className="claude-heading">{heading2}</h2> : ''}
            {desc ? <p className="claude-description">{desc}</p> : ''}
            {btnVersion ? <CustomButton version={btnVersion} width='100%'>Talk to VITA</CustomButton>: ''}
        </div>
    );
}

export default GridLayout;