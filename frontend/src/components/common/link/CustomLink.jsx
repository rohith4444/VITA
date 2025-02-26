import React from "react";
// import './button.css';
import { Link } from "@mui/material";
import { styled } from '@mui/material/styles';
import Icon from '@mui/material/Icon';

const StyledLinkV1 = styled(Link)(({ theme }) => ({
    display: 'flex',
    alignItems: 'center',
    textDecoration: 'none',
    // color: props.version === 'v1' ? theme.palette.primary : theme.palette.secondary
}));

const StyledLinkV2 = styled(Link)(({ theme }) => ({
    display: 'flex',
    alignItems: 'center',
    textDecoration: 'none',
    color: "black"
}));

export default function CustomLink({ ...props }) {
    var className = props.version + " ";
    if (props.version === "v1") {
        return (<StyledLinkV1 {...props}>{props.children}<Icon>{props.icon}</Icon></StyledLinkV1>);
    } else if (props.version === 'v2') {
        return (<StyledLinkV2 {...props}>{props.children}<Icon>{props.icon}</Icon></StyledLinkV2>);
    }
}