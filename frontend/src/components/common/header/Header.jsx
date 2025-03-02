import React, { useState } from "react";
import Stack from '@mui/material/Stack';
import './header.css';
import CustomButton from "../button/CustomButton";
import Logo from "../logo/Logo";
import CustomLink from "../link/CustomLink";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { Menu, MenuItem } from "@mui/material";
import { AppBar, Toolbar, Button, Typography } from "@mui/material";
import { ArrowRight, MenuRounded as MenuIcon } from "@mui/icons-material";
import { Route, useNavigate } from "react-router-dom";
import { useTheme } from '@mui/material/styles';

export default function Header() {
    const theme = useTheme();

    const [anchorEl, setAnchorEl] = useState(null);
    const [open, setOpen] = useState(false);
    const [anchorEl1, setAnchorEl1] = useState(null);
  const [nestedAnchorEl, setNestedAnchorEl] = useState(null);
  const [moreNestedAnchorEl, setMoreNestedAnchorEl] = useState(null);

  const navigate = useNavigate();

  // Handle main menu open/close
  const handleMenuOpen = (event) => {
    setAnchorEl1(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl1(null);
    setNestedAnchorEl(null);
    setMoreNestedAnchorEl(null);
  };

  // Handle nested menu open/close
  const handleNestedMenuOpen = (event) => {
    setNestedAnchorEl(event.currentTarget);
  };

  const handleMoreNestedMenuOpen = (event) => {
    setMoreNestedAnchorEl(event.currentTarget);
  };
    //   const open = Boolean(anchorEl);
    
      const handleClick = (event) => {
        setAnchorEl(event.currentTarget);
        setOpen(true);
      };
    
      const handleClose = () => {
        setAnchorEl(null);
        setOpen(false);
        navigate('/vitahomepage');
      };
    return (
        <div class="header">
            <div class="icon" onClick={() => navigate("/")}>
                <Logo width={50} height={70} strokeWidth={15} stroke={theme.palette.secondary.dark} />
                <h2>AETHER AI</h2>
            </div>
            <div class="navBar">
                <Stack spacing={3} direction="row" sx={{alignItems: "center"}}>
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
                        <MenuItem onClick={handleClose}>Overview</MenuItem>
                        <MenuItem onClick={handleClose}>Agents</MenuItem>
                    </Menu>
                    <CustomLink href="/research" version="v1" underline="hover">Research</CustomLink>
                    <CustomLink href="/company" version="v1" underline="hover">Company</CustomLink>
                    <CustomLink href="/news" version="v1" underline="hover">News</CustomLink>
                    <CustomButton version="v1" bgColor={theme.palette.secondary.main} onClick={() => navigate("/login")}>Try Vita</CustomButton>
                </Stack>
            </div>
            <div class="navBarMenu">
                {/* <CustomButton
                    version='v2'
                    bgColor={theme.palette.secondary.main}
                    onClick={handleMenuOpen}
                    startIcon={<MenuIcon />}
                    >
                        <MenuIcon />
                    </CustomButton> */}
                    <MenuIcon fontSize="large" color={theme.palette.secondary.main} onClick={handleMenuOpen} />
                {/* Main Menu */}
                <Menu className="menuDropdown" anchorEl={anchorEl1} open={Boolean(anchorEl1)} onClose={handleMenuClose}>
                    <Stack spacing={1} direction="column" sx={{alignItems: "center"}}>
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
                            <MenuItem onClick={handleClose}>Overview</MenuItem>
                            <MenuItem onClick={handleClose}>Agents</MenuItem>
                        </Menu>
                        <CustomLink href="#" version="v1" underline="hover">Research</CustomLink>
                        <CustomLink href="#" version="v1" underline="hover">Company</CustomLink>
                        <CustomLink href="#" version="v1" underline="hover">News</CustomLink>
                        <CustomButton variant="contained" bgColor={theme.palette.secondary.main} version="v1" onClick={() => navigate("/login")}>Try Vita</CustomButton>
                    </Stack>
                </Menu>

                {/* Nested Menu */}
                <Menu anchorEl={nestedAnchorEl} open={Boolean(nestedAnchorEl)} onClose={handleMenuClose}>
                    <MenuItem onClick={handleMenuClose}>Web Development</MenuItem>
                    <MenuItem onClick={handleMoreNestedMenuOpen}>
                        Design <ArrowRight fontSize="small" />
                    </MenuItem>
                </Menu>

                {/* More Nested Menu */}
                <Menu anchorEl={moreNestedAnchorEl} open={Boolean(moreNestedAnchorEl)} onClose={handleMenuClose}>
                    <MenuItem onClick={handleMenuClose}>UI/UX Design</MenuItem>
                    <MenuItem onClick={handleMenuClose}>Graphic Design</MenuItem>
                </Menu>
            </div>
        </div>
    )
}