import React from "react";
import "./login.css";

const Login = () => {
  return (
    <div className="landing-container">
      <div className="landing-content">
        {/* Left Section */}
        <div className="left-section">
          {/* <div className="logo">✷ Claude</div> */}
          <h1 className="tagline">Your ideas, amplified</h1>
          <p className="subtext">Privacy-first AI that helps you create in confidence.</p>
          
          <div className="login-box">
            <button className="google-login">
              <span style={{ marginRight: 8 }}>🔵</span> Continue with Google
            </button>
            <p className="or-text">OR</p>
            <input type="email" placeholder="Enter your personal or work email" className="email-input" />
            <button className="email-login">Continue with email</button>
            <p className="terms-text">
              By continuing, you agree to Anthropic’s <a href="#">Consumer Terms</a> and <a href="#">Privacy Policy</a>.
            </p>
          </div>

          <p className="learn-more">Learn more ↓</p>
        </div>

        {/* Right Section */}
        <div className="right-section">
          <div className="chat-bubble">
            <img
              src="https://via.placeholder.com/24" 
              alt="User Avatar"
              style={{ borderRadius: "50%", marginRight: "8px" }}
            />
            Claude, create a report to analyze product usage and user feedback.
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;