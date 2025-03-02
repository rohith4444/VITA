import './App.css';
import { BrowserRouter, Routes, Route, useParams } from "react-router-dom";
import Login from './components/login/Login';
import Main from './components/mainpage/Main';
import Homepage from './components/vita-homepage/Homepage';
import VitaLoginPage from './components/vita-login-page/VitaLoginPage';
import Research from './components/research/Research';
import News from './components/news/News';
import Header from './components/common/header/Header';
import Footer from './components/common/footer/Footer';
import Company from './components/company/Company';
import TestComponent from './components/testcomponent/TestComponent';

{/* const ProfileComponentWrapper = () => {
  const { username } = useParams();
  return <ProfileComponent username={username} />;
};
<Route
  path='/u/:username/'
  element={<ProfileComponentWrapper />}
/> */}

function App() {

  const ProjectPageWrapper = () => {
    const { chatId, projectId } = useParams();
    return <VitaLoginPage defaultState="project" defaultChatId={chatId} defaultProjectId={projectId} />;
  };

  const ChatPageWrapper = () => {
    const { chatId, projectId } = useParams();
    return <VitaLoginPage defaultState="chat" defaultChatId={chatId} defaultProjectId={projectId} />;
  };

  return (
    <div className="App">
      <div class="container">
        <BrowserRouter>
          {/* <Header /> */}
          <Routes>
            <Route path="/" element={<Main />} />
            {/* <Route index element={<Home />} /> */}
            <Route path="/login" element={<Login />} />
            <Route path="/research" element={<Research />} />
            <Route path="/company" element={<Company />} />
            <Route path="/news" element={<News />} />
            <Route path="/vitahomepage" element={<Homepage />} />
            <Route path="/vitaloginpage" element={<VitaLoginPage />} />
            <Route path="/vitaloginpage/chat/:chatId" element={<ChatPageWrapper />} />
            <Route path="/vitaloginpage/project/:projectId" element={<ProjectPageWrapper />} />
            <Route path="/vitaloginpage/project/:projectId/:chatId" element={<ProjectPageWrapper />} />
            <Route path='/test' element={<TestComponent />} />
          </Routes>
          {/* <Footer /> */}
        </BrowserRouter>
      </div>
    </div>
  );
}

export default App;
