import { TextFieldsOutlined } from "@mui/icons-material";
import { TextField } from "@mui/material";
import { withStyles } from "@mui/styles";
import React from "react";

//declare the const and add the material UI style
const CssTextField = withStyles({
    root: {
      '& label': {
        color: 'black',
      },
      '& label.Mui-focused': {
        color: 'black',
      },
      '& .MuiInput-underline:after': {
        borderBottomColor: 'black',
      },
      '& .MuiOutlinedInput-root': {
        '& fieldset': {
          borderColor: 'gray',
        },
        '&:hover fieldset': {
          borderColor: 'gray',
        },
        '&.Mui-focused fieldset': {
          borderColor: 'gray',
        },
      },
    },
  })(TextField);

const TextInput = ({ ...props }) => {
    return (
        <CssTextField {...props} />
    );
}

export default TextInput;