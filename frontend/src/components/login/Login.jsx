import React, { useState } from "react";
import "./login.css";
import CustomButton from "../common/button/CustomButton";
import TextInput from "../common/textinput/TextInput";
import Header from "../common/header/Header";
import Footer from "../common/footer/Footer";
import { useNavigate } from "react-router-dom";
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import { useTheme } from '@mui/material/styles';

const Login = () => {
  const theme = useTheme()
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState("login");

  const handleTabValueChange = (event, newValue) => {
    setTabValue(newValue);
  }

  return (
    <>
      <Header />
      <div className="landing-container">
        <div className="login-card-container">
          <div className="card login-card">
            <div className="login-register-buttons">
              <Tabs
                className="tabs"
                value={tabValue}
                onChange={handleTabValueChange}
                // textColor="secondary"
                // indicatorColor="secondary"
                indicatorColor="secondary"
                textColor="secondary"
                variant="fullWidth"
                aria-label="full width secondary tabs example"
              >
                <Tab value="login" label="Login" id='full-width-tab-0' aria-controls='full-width-tabpanel-0' />
                <Tab value="register" label="Register" id='full-width-tab-1' aria-controls='full-width-tabpanel-1' />
              </Tabs>
            </div>
            {tabValue === "login" ? <>
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
                <div className="login-form-field login-button">
                  <CustomButton version="v1" width="50%" color="secondary"  bgColor={theme.palette.secondary.main} onClick={() => navigate("/vitaloginpage")}>Login</CustomButton>
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
                  <TextInput label="Re-enter password" id="outlined-size-small" size="small" className="login-form-field" />
                </div>
                <div className="login-form-field login-button">
                  <CustomButton version="v1" width="50%" bgColor={theme.palette.secondary.main}>Register</CustomButton>
                </div>
              </>
            }
          </div>
        </div>
      </div>
      {/* <Footer /> */}
    </>
  );
};

export default Login;