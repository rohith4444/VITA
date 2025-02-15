import React from "react";
import './footer.css';
import CustomLink from "../link/CustomLink";
import Stack from '@mui/material/Stack';
import XIcon from '@mui/icons-material/X';
import FacebookIcon from '@mui/icons-material/Facebook';
import InstagramIcon from '@mui/icons-material/Instagram';
import LinkedInIcon from '@mui/icons-material/LinkedIn';

const Footer = () => {
    return (
        <div class="item footer">
            <div class="topFooter">
                <div className="topleftFooter">
                    <Stack spacing={5} direction="row" sx={{alignItems: "center"}}>
                        <CustomLink href="#" version="v2" underline="hover">About Aether AI</CustomLink>
                        <CustomLink href="#" version="v2" underline="hover">Contact Us</CustomLink>
                        <CustomLink href="#" version="v2" underline="hover">Careers</CustomLink>
                        <CustomLink href="#" version="v2" underline="hover">Terms of Service</CustomLink>
                    </Stack>
                </div>
                <div className="topRightFooter">
                    <Stack spacing={1} direction="row" sx={{alignItems: "center"}}>
                        <CustomLink href="#" version="v2" underline="hover"><FacebookIcon /></CustomLink>
                        <CustomLink href="#" version="v2" underline="hover"><InstagramIcon /></CustomLink>
                        <CustomLink href="#" version="v2" underline="hover"><LinkedInIcon /></CustomLink>
                        <CustomLink href="#" version="v2" underline="hover"><XIcon /></CustomLink>
                    </Stack>
                </div>
            </div>
            <div class="bottomFooter">
                {/* bottom */}
            </div>
        </div>
    );
}

export default Footer;