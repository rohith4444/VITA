import React from "react";
import './workwithus.css';
import CustomButton from "../../common/button/CustomButton";

const WorkWithUs = () => {
    return (
        <>
            <div className="work-card">
                <img alt="Office" className="work-image" />
                <div className="work-content">
                    <h2 className="work-heading">Work with Anthropic</h2>
                    <p className="work-description">
                    Anthropic is an AI safety and research company based in San Francisco. Our interdisciplinary 
                    team has experience across ML, physics, policy, and product. Together, we generate research 
                    and create reliable, beneficial AI systems.
                    </p>
                    <CustomButton version='bv1' variant='outlined'>See open roles</CustomButton>
                    <button className="work-button">See open roles</button>
                </div>
            </div>
        </>
    );
};

export default WorkWithUs;