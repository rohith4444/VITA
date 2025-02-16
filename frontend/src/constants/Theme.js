import { createTheme } from '@material-ui/core/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#000000',
    },
    secondary: {
      main: "#f6af3b",
    }
  },
  typography: {
    button: {
      textTransform: 'none'
    }
  }
});

export default theme;

// .palette.primary
// .palette.secondary
// .palette.error
// .palette.warning
// .palette.info
// .palette.success

// const primary = {
//   main: '#1976d2',
//   light: '#42a5f5',
//   dark: '#1565c0',
//   contrastText: '#fff',
// };