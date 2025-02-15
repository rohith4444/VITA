import { React } from "react";
import "./ourwork.css";

const workItems = [
  {
    category: "Product",
    title: "Claude for Enterprise",
    date: "Sep 4, 2024",
  },
  {
    category: "Alignment · Research",
    title: "Constitutional AI: Harmlessness from AI Feedback",
    date: "Dec 15, 2022",
  },
  {
    category: "Announcements",
    title: "Core Views on AI Safety: When, Why, What, and How",
    date: "Mar 8, 2023",
  },
];

const OurWork = () => {
  return (
    <div className="our-work-container">
      <h2 className="our-work-title">Our Work</h2>
      <div className="our-work-cards">
        {workItems.map((item, index) => (
          <div key={index} className="our-work-card">
            <p className="our-work-category">{item.category}</p>
            <h3 className="our-work-title">{item.title}</h3>
            <p className="our-work-date">{item.date}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default OurWork;