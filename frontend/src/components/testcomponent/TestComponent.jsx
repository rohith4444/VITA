import React, { useState, useRef } from "react";
import "./testcomponent.css"; // Import the CSS file

const TestComponent = () => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div>
      {/* Button to open sidebar */}
      <button className="open-sidebar-btn" onClick={() => setIsVisible(true)}>
        Open Sidebar
      </button>

      {/* Sidebar */}
      <div className={`sidebar ${isVisible ? "visible" : ""}`}>
        {/* Close Button */}
        <button className="close-btn" onClick={() => setIsVisible(false)}>✖</button>

        {/* Sidebar Options */}
        <ul className="sidebar-options">
          <li>🏠 Home</li>
          <li>📁 Projects</li>
          <li>🔧 Settings</li>
          <li>📞 Contact</li>
        </ul>
      </div>
    </div>
  );// 
};

export default TestComponent;
