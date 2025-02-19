import React from "react";
import './footer.css';
import CustomLink from "../link/CustomLink";
import Stack from '@mui/material/Stack';
import XIcon from '@mui/icons-material/X';
import FacebookIcon from '@mui/icons-material/Facebook';
import InstagramIcon from '@mui/icons-material/Instagram';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import Logo from "../logo/Logo";

const Footer = () => {
    return (
        <div class="item footer">
            <div class="topFooter">
                <div className="topLeftFooter">
                    <Logo width={150} height={150} strokeWidth={5} />
                </div>
                <div className="topRightFooter">
                    <Stack spacing={{ xs: 1, sm: 1, md: 3 }} direction={{ xs: 'column', sm: 'column', md: 'column' }} sx={{alignItems: "center"}}>
                        <CustomLink href="#" version="v2" underline="hover">About Aether AI</CustomLink>
                        <CustomLink href="#" version="v2" underline="hover">Contact Us</CustomLink>
                        <CustomLink href="#" version="v2" underline="hover">Careers</CustomLink>
                        <CustomLink href="#" version="v2" underline="hover">Terms of Service</CustomLink>
                    </Stack>
                </div>
            </div>
            <div class="bottomFooter">
                <div class="app-icons">
                    <a href="https://apps.apple.com/app/id1551353775">
                        <img 
                        class="apple"
                        src="https://tools.applemediaservices.com/api/badges/download-on-the-app-store/black/en-us?size=250x83&amp;releaseDate=1276560000&h=7e7b68fad19738b5649a1bfb78ff46e9" 
                        alt="Download on the App Store" />
                    </a>
                    <a href='https://play.google.com/store/apps/details?id=com.stagescycling.stages'>
                        <img 
                        class="android" 
                        alt='Get it on Google Play' 
                        src='https://play.google.com/intl/en_us/badges/images/generic/en_badge_web_generic.png' />
                    </a>
                </div>
                <div className="social-media">
                    <Stack spacing={1} direction='row' sx={{alignItems: "center"}}>
                        <CustomLink href="#" version="v2" underline="hover"><FacebookIcon /></CustomLink>
                        <CustomLink href="#" version="v2" underline="hover"><InstagramIcon /></CustomLink>
                        <CustomLink href="#" version="v2" underline="hover"><LinkedInIcon /></CustomLink>
                        <CustomLink href="#" version="v2" underline="hover"><XIcon /></CustomLink>
                    </Stack>
                </div>
            </div>
        </div>
    );
}

export default Footer;