import React from "react";
import Button from '@mui/material/Button';
import './button.css';
import styled from 'styled-components';

const ButtonV2 = styled.button`
    background-color: white;
    color: ${props => props.bgColor ? props.bgColor : "black"};
    font-size: 14px;
    font-weight: 600;
    border: 1px solid ${props => props.bgColor ? props.bgColor : "black"};
    border-radius: 8px;
    cursor: pointer;
    width: ${props => props.width ? props.width : 'auto'};
    margin: ${props => props.margin ? props.margin: '0px'};
    padding: ${props => props.padding ? props.padding : '12px 20px'};
    transition: all 0.3s ease-in-out;
    &:hover {
        background-color: ${props => props.bgColor ? props.bgColor : "black"};
        border: 1px solid ${props => props.bgColor ? props.bgColor : "black"};
        color: white;
    }
`

const ButtonV1 = styled.button`
    background-color: ${props => props.bgColor ? props.bgColor : 'black'};
    color: white;
    font-size: 14px;
    font-weight: 600;
    border: 1px solid ${props => props.bgColor ? props.bgColor : 'black'};
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
    width: ${props => props.width ? props.width : 'auto'};
    margin: ${props => props.margin ? props.margin: '0px'};
    padding: ${props => props.padding ? props.padding : '12px 20px'};
`

export default function CustomButton({ version, ...props }) {
    var className = version + " ";
    className = className + props.variant;
    if (version === "v1") {
        return <ButtonV1 {...props}>{props.children}</ButtonV1>
    }
    if (version === "v2") {
        return <ButtonV2 {...props}>{props.children}</ButtonV2>
    }
    return (<Button className={className} {...props}>{props.children}</Button>);
}