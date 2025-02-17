import {React} from 'react';
import './main.css';
import CustomButton from '../common/button/CustomButton';
import GridLayout from '../common/gridlayout/GridLayout';
import WorkWithUs from './workwithus/WorkWithUs';
import OurWork from './ourwork/OurWork';
import Header from '../common/header/Header';
import Footer from '../common/footer/Footer';

const Main = () => {
    return (
        <>
            <Header />
            <div class="item mainblock">
                <div class="mainblockTopLeft">
                    <div class="mainblockTopLeftTop">
                        <h1>AI research and products that put safety at the frontier</h1>
                    </div>
                    <div class="mainblockTopLeftBottom">
                        <GridLayout btnVersion='v1' heading1='VITA.AI' heading2='Meet VITA' desc='Claude 3.5 Sonnet, our most intelligent AI model, is now available.' />
                        <GridLayout btnVersion='v2' heading1='API' heading2='Build with VITA' desc='Create AI-powered applications and custom experiences using Claude.'/>
                    </div>
                </div>
                <div class="mainblockTopRight">
                    {/* Top Right */}
                </div>
            </div>
            <OurWork />
            <WorkWithUs />
            <Footer />
        </>
    );
}

export default Main;