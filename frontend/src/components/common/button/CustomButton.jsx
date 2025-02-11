import React from "react";
import Button from '@mui/material/Button';
import './button.css';

export default function CustomButton({ ...props }) {
    var className = props.version + " ";
    className = className + props.variant;

    return (<Button className={className} sx={{ml:6, textTransform: 'camelcase'}} variant={props.variant}>{props.children}</Button>);
}