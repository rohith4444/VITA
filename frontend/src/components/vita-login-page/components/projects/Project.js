import React from "react";
import './project.css';
import TextInput from "../../../common/textinput/TextInput";
import CustomButton from "../../../common/button/CustomButton";

const projects = [
    { title: "AETHER AI", description: "description", updated: "1 day ago" },
    { title: "VITA", description: "description", updated: "1 month ago" },
    { title: "Integrate DDS and dev py Package", description: "description", updated: "6 months ago" },
    { title: "Comp-HuSim", description: "description", updated: "6 months ago" },
    { title: "LinDer", description: "description", updated: "6 months ago" },
    { title: "How to use Claude", description: "description", updated: "6 months ago" }
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
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                <div className="project-card" key="0">
                    <h3 className="project-title">Title</h3>
                    <p className="project-description">Description</p>
                    <p className="project-updated">Updated</p>
                </div>
                {/* {projects.map((project, index) => (
                    <div className="project-card">
                        <h3 className="project-title">{project.title}</h3>
                        <p className="project-description">{project.description}</p>
                        <p className="project-updated">Updated {project.updated}</p>
                    </div>
                ))} */}
            </div>
        </div>
    );
}

export default Project