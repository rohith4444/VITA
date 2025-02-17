import React, { useState } from "react";
import "./login.css";
import CustomButton from "../common/button/CustomButton";
import TextInput from "../common/textinput/TextInput";
import Header from "../common/header/Header";
import Footer from "../common/footer/Footer";

const Login = () => {

  const [login, setLogin] = useState(true);

  return (
    <>
      <Header />
      <div className="landing-container">
        <div className="login-card">
          <div className="login-register-buttons">
            <CustomButton version="v2" width='calc(50% - 20px)' margin="10px" onClick={() => setLogin(true)}>Login</CustomButton>
            <CustomButton version="v2" width='calc(50% - 20px)' margin="10px"onClick={() => setLogin(false)}>Register</CustomButton>
          </div>
          {login ? <>
              <div className="text">
                <p>Sign in with: </p>
                <p>or: </p>
              </div>
              <div className="login-form-field">
                <TextInput label="Enter email or username" id="outlined-size-small" size="small" className="login-form-field" />
              </div>
              <div className="login-form-field">
                <TextInput label="Enter password" id="outlined-size-small" size="small" className="login-form-field" />
              </div>
              <div className="login-form-field forgot-password">
                <p>Forgot password?</p>
              </div>
              <div className="login-form-field">
                <CustomButton version="v1" width="50%">Login</CustomButton>
              </div>
            </> : 
            <>
              <div className="login-form-field">
                <TextInput label="Enter first name" id="outlined-size-small" size="small" className="login-form-field" />
              </div>
              <div className="login-form-field">
                <TextInput label="Enter last name" id="outlined-size-small" size="small" className="login-form-field" />
              </div>
              <div className="login-form-field">
                <TextInput label="Enter email" id="outlined-size-small" size="small" className="login-form-field" />
              </div>
              <div className="login-form-field">
                <TextInput label="Enter password" id="outlined-size-small" size="small" className="login-form-field" />
              </div>
              <div className="login-form-field">
                <TextInput label="Re-Enter password" id="outlined-size-small" size="small" className="login-form-field" />
              </div>
              <div className="login-form-field">
                <CustomButton version="v1" width="50%">Register</CustomButton>
              </div>
            </>
          }
        </div>
      </div>
      <Footer />
    </>
  );
};

export default Login;