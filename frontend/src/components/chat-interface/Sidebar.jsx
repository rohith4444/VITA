import React, { useState } from "react";

const Sidebar = ({ onSelectProject, ...props }) => {
    const [collapsed, setCollapsed] = useState(false);
    const [selectedProject, setSelectedProject] = useState("Chat Interface Design");

    const toggleSidebar = () => {
        setCollapsed(!collapsed);
    };

    const projects = [
        "Web page with color",
        "Color theme suggestions",
        "Chat interface design",
        "Modern table design"
    ];

    return (
        <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>
        <div className="sidebar-header">
            {!collapsed && <span>Projects</span>}
            <span className="toggle-btn" onClick={toggleSidebar}>
            {collapsed ? "▶" : "◀"}
            </span>
        </div>
        {projects.map((project) => (
            <div
            key={project}
            className={`sidebar-item ${selectedProject === project ? "active" : ""}`}
            onClick={() => {
                setSelectedProject(project);
                onSelectProject(project);
            }}
            >
            {!collapsed && project}
            </div>
        ))}
        </div>
    );
}

export default Sidebar;