import React, { useState } from "react";
import Stack from '@mui/material/Stack';
import './header.css';
import CustomButton from "../button/CustomButton";
import Logo from "../logo/Logo";
import CustomLink from "../link/CustomLink";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { Menu, MenuItem } from "@mui/material";

export default function Header() {

    const [anchorEl, setAnchorEl] = useState(null);
    const [open, setOpen] = useState(false);
    //   const open = Boolean(anchorEl);
    
      const handleClick = (event) => {
        setAnchorEl(event.currentTarget);
        setOpen(true);
      };
    
      const handleClose = () => {
        setAnchorEl(null);
        setOpen(false);
      };
    return (
        <div class="item">
            <header class="header flex">
                <div class="icon">
                    <Logo width={50} height={70} strokeWidth={15} />
                    <h4>Aether AI</h4>
                </div>
                <div class="navBar">
                    <Stack spacing={5} direction="row" sx={{alignItems: "center"}}>
                        <CustomLink href="#" version="v1" underline="hover" onClick={handleClick} 
                        icon={open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                        >
                            Vita
                        </CustomLink>
                        <Menu
                            anchorEl={anchorEl}
                            open={open}
                            onClose={handleClose}
                        >
                            <MenuItem onClick={handleClose}>Option 1</MenuItem>
                            <MenuItem onClick={handleClose}>Option 2</MenuItem>
                            <MenuItem onClick={handleClose}>Option 3</MenuItem>
                        </Menu>
                        <CustomLink href="#" version="v1" underline="hover">Research</CustomLink>
                        <CustomLink href="#" version="v1" underline="hover">Company</CustomLink>
                        <CustomLink href="#" version="v1" underline="hover">News</CustomLink>
                        <CustomButton variant="contained" version="v1">Try Vita</CustomButton>
                    </Stack>
                </div>
            </header>
        </div>
    )
}