import React from "react";
import './project.css';
import TextInput from "../../../common/textinput/TextInput";
import CustomButton from "../../../common/button/CustomButton";

const projects = [
    { title: "AETHER AI", description: "I'm building an AI-Powered Project Development Platform...", updated: "1 day ago" },
    { title: "VITA", description: "This project aims to develop an intelligent multi-agent...", updated: "1 month ago" },
    { title: "Integrate DDS and dev py Package", description: "Turning Demographic sampling tool into a Python package...", updated: "6 months ago" },
    { title: "Comp-HuSim", description: "A software stack for using LLMs to create complex personas...", updated: "6 months ago" },
    { title: "LinDer", description: "A project which translates speech to text and vice versa...", updated: "6 months ago" },
    { title: "How to use Claude", description: "An example project that also doubles as a how-to guide...", updated: "6 months ago" }
];

const Project = ({ newProject, ...props }) => {
    return (
        <div className="projects-wrapper">
            <div className="top-search">
                <div className="left-new-project">
                    <TextInput size="small"/>
                    <CustomButton>Search</CustomButton>
                </div>
                {newProject && <div className="right-search-project">
                    <TextInput size="small"/>
                    <CustomButton>Add Project</CustomButton>
                </div>}
            </div>
            <div className="recent-projects">
                {projects.map((project, index) => (
                    <div className="project-card" key={index}>
                        <h3 className="project-title">{project.title}</h3>
                        <p className="project-description">{project.description}</p>
                        <p className="project-updated">Updated {project.updated}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Project