import React from "react";
import Button from '@mui/material/Button';
import './button.css';
import styled from 'styled-components';

const ButtonV2 = styled.button`
    background-color: white;
    color: black;
    font-size: 14px;
    font-weight: 600;
    padding: 12px 20px;
    border: 2px solid black;
    border-radius: 8px;
    cursor: pointer;
    width: ${props => props.width ? props.width : 'auto'};
    transition: all 0.3s ease-in-out;
    &:hover {
        background-color: black;
        color: white;
    }
`

const ButtonV1 = styled.button`
    background-color: black;
    color: white;
    font-size: 14px;
    font-weight: 600;
    padding: 12px 20px;
    border: 2px solid black;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
    width: ${props => props.width ? props.width : 'auto'};
`

export default function CustomButton({ version, ...props }) {
    var className = version + " ";
    className = className + props.variant;
    if (version == "v1") {
        return <ButtonV1 {...props}>{props.children}</ButtonV1>
    }
    if (version == "v2") {
        return <ButtonV2 {...props}>{props.children}</ButtonV2>
    }
    return (<Button className={className} {...props}>{props.children}</Button>);
}