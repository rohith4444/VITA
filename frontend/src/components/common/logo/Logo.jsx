import * as React from "react";
const Logo = (props) => (
  <svg viewBox="0 0 200 200"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <line x1={40} y1={180} x2={120} y2={40} stroke={props.stroke ? props.stroke : "black"} strokeWidth={props.strokeWidth} strokeLinecap="round" />
    <line x1={120} y1={40} x2={160} y2={40} stroke={props.stroke ? props.stroke : "black"} strokeWidth={props.strokeWidth} strokeLinecap="round" />
    <line x1={60} y1={95} x2={160} y2={95} stroke={props.stroke ? props.stroke : "black"} strokeWidth={props.strokeWidth} strokeLinecap="round" />
    <line x1={120} y1={150} x2={160} y2={150} stroke={props.stroke ? props.stroke : "black"} strokeWidth={props.strokeWidth} strokeLinecap="round" />
    <line x1={120} y1={40} x2={120} y2={150} stroke={props.stroke ? props.stroke : "black"} strokeWidth={props.strokeWidth} strokeLinecap="round" />
    {/* <circle r={props.strokeWidth - 2} cx={120} cy={20 - (props.strokeWidth/2)} fill="black" /> */}
  </svg>
);
export default Logo;
