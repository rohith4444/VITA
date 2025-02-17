import './App.css';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Chat from './components/chat-interface/Chat';
import Login from './components/login/Login';
import Main from './components/mainpage/Main';
import Homepage from './components/vita-homepage/Homepage';

function App() {
  return (
    <div className="App">
      <div class="container">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Main />}/ >
            {/* <Route index element={<Home />} /> */}
            <Route path="/login" element={<Login />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/vitahomepage" element={<Homepage />} />
          </Routes>
        </BrowserRouter>
      </div>
    </div>
  );
}

export default App;
