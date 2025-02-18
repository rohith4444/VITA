import './App.css';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from './components/login/Login';
import Main from './components/mainpage/Main';
import Homepage from './components/vita-homepage/Homepage';
import VitaLoginPage from './components/vita-login-page/VitaLoginPage';

function App() {
  return (
    <div className="App">
      <div class="container">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Main />}/ >
            {/* <Route index element={<Home />} /> */}
            <Route path="/login" element={<Login />} />
            <Route path="/vitahomepage" element={<Homepage />} />
            <Route path="/vitaloginpage" element={<VitaLoginPage />} />
          </Routes>
        </BrowserRouter>
      </div>
    </div>
  );
}

export default App;
