import { createTheme } from '@material-ui/core/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#000000',
    },
    secondary: {
      main: '#7B592B',
      light: '#A37C44',
      dark: '#543A14',
      contrastText: '#FFFFFF'
    },
    success: {
      main: '#3A574A',
      light: '#5D7D6E',
      dark: '#293D33',
      contrastText: '#FFFFFF'
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