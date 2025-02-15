import React from "react";
import './gridlayout.css';
import CustomButton from "../button/CustomButton";

const GridLayout = ({ heading1, heading2, desc, btnVariant,  ...props }) => {
    if (btnVariant == null) {
        btnVariant = 'outlined'
    }
    return (
        <div className="claude-card">
            <p className="claude-title">{heading1}</p>
            {heading2 ? <h2 className="claude-heading">{heading2}</h2> : ''}
            {desc ? <p className="claude-description">{desc}</p> : ''}
            {btnVariant ? <CustomButton version='bv4' variant={btnVariant}>Talk to Claude</CustomButton>: ''}
        </div>
    );
}

export default GridLayout;