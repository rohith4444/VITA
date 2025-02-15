import './App.css';
import Chat from './components/chat-interface/Chat';
import Footer from './components/common/footer/Footer';
import Header from './components/common/header/Header';
import Login from './components/login/Login';
import Main from './components/mainpage/Main';

function App() {
  return (
    <div className="App">
      <div class="container">
        <Header />
        {/* <Main /> */}
        {/* <Chat /> */}
        <Login />
        <Footer />
      </div>
    </div>
  );
}

export default App;
