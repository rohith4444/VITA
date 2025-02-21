import React from "react";
import './homepage.css';
import Header from "../common/header/Header";
import Footer from "../common/footer/Footer";
import CustomButton from "../common/button/CustomButton";
import { AccountTree, Devices, Storage, BugReport, Rocket, Create, GroupAdd, Code, Refresh, Lightbulb, LaptopMac, Business, School } from '@mui/icons-material';
import { Divider } from "@mui/material";

const aiAgents = [
    {
        icon: <AccountTree fontSize="large" />, 
        title: "Project Manager AI",
        description: "Breaks down requirements and plans execution."
    },
    {
        icon: <Devices fontSize="large" />, 
        title: "Frontend Developer AI",
        description: "Crafts responsive and dynamic user interfaces."
    },
    {
        icon: <Storage fontSize="large" />, 
        title: "Backend Developer AI",
        description: "Builds scalable and secure server-side logic."
    },
    {
        icon: <BugReport fontSize="large" />, 
        title: "Testing AI",
        description: "Ensures reliability with automated test cases."
    },
    {
        icon: <Rocket fontSize="large" />, 
        title: "Deployment AI",
        description: "Helps push your code live seamlessly."
    }
];

const steps = [
    {
        icon: <Create fontSize="large" />, 
        title: "Describe Your Project",
        description: "Tell VITA what you need—whether it's a simple website, a complex application, or a new API."
    },
    {
        icon: <GroupAdd fontSize="large" />, 
        title: "AI Agents Collaborate",
        description: "VITA’s project manager, developers, and testers work together to generate and refine the code."
    },
    {
        icon: <Code fontSize="large" />, 
        title: "Get Fully Functional Code",
        description: "Receive structured, documented, and executable code tailored to your requirements."
    },
    {
        icon: <Refresh fontSize="large" />, 
        title: "Iterate & Improve",
        description: "Modify, extend, and enhance your project effortlessly with VITA’s continuous support."
    }
];

const useCases = [
    {
        icon: <Lightbulb fontSize="large" />,
        title: "Startups & Entrepreneurs",
        description: "Quickly prototype and build MVPs with AI-generated code."
    },
    {
        icon: <LaptopMac fontSize="large" />,
        title: "Developers",
        description: "Speed up coding and get assistance with complex tasks."
    },
    {
        icon: <Business fontSize="large" />,
        title: "Enterprises",
        description: "Automate software development and reduce costs."
    },
    {
        icon: <School fontSize="large" />,
        title: "Students & Learners",
        description: "Generate code while understanding best practices."
    }
];

const Homepage = () => {
    return (
        <>
            {/* <Header /> */}
            <div className="top-section">
                <div className="left-section">
                    <div className="card">
                    <h2>VITA: Your AI-Powered Software Development Team</h2>
                    <p>From idea to execution—VITA builds production-ready code with intelligent agents handling project management, development, and testing.</p>
                    <CustomButton version="v1">Try Vita</CustomButton>
                    </div>
                </div>
                <div className="right-section">
                    {/* right section */}
                </div>
            </div>
            <div className="ai-agents">
                <h2 className="ai-agents-heading">A Virtual Team for Every Development Need</h2>
                <p className="ai-agents-text">
                    VITA consists of specialized AI agents, each handling different aspects of software development.
                </p>
                <div className="ai-agents-cards">
                    {aiAgents.map((agent, index) => (
                        <div key={index} className="ai-agents-card">
                            <div className="text-blue-500 mb-4">{agent.icon}</div>
                            <h3 className="text-xl font-semibold mb-2">{agent.title}</h3>
                            <p className="text-gray-600">{agent.description}</p>
                        </div>
                    ))}
                </div>
            </div>
            <Divider />
            <div className="ai-agents">
                <h2 className="ai-agents-heading">From Concept to Code in Just a Few Steps</h2>
                <p className="ai-agents-text">
                    VITA streamlines software development through a structured and efficient process.
                </p>
                <div className="ai-agents-cards">
                    {steps.map((step, index) => (
                        <div key={index} className="ai-agents-card">
                            <div className="text-blue-500 mb-4">{step.icon}</div>
                            <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                            <p className="text-gray-600">{step.description}</p>
                        </div>
                    ))}
                </div>
            </div>
            <div className="usecases">
                <h2 className="usecases-title">VITA is Perfect for...</h2>
                <div className="usecases-timeline">
                    {useCases.map((useCase, index) => (
                        <div key={index} className="usecases-timeline-item">
                            <div className="usecases-timeline-icon">{useCase.icon}</div>
                            <div className="usecases-timeline-content">
                                <h3 className="usecase-title">{useCase.title}</h3>
                                <p className="usecase-description">{useCase.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            {/* <Footer /> */}
        </>
    );
}

export default Homepage;