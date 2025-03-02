import { TextFieldsOutlined } from "@mui/icons-material";
import { TextField } from "@mui/material";
import { withStyles } from "@mui/styles";
import React from "react";

//declare the const and add the material UI style
const CssTextField = withStyles(theme => ({
    root: {
      '& label': {
        color: theme.palette.secondary.dark,
      },
      '& label.Mui-focused': {
        color: theme.palette.secondary.dark,
      },
      '& .MuiInput-underline:after': {
        borderBottomColor: theme.palette.secondary.dark,
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
  }))(TextField);

const TextInput = ({ ...props }) => {
    return (
        <CssTextField {...props} />
    );
}

export default TextInput;