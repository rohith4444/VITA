import React from 'react';

const ColorPalette = () => {
  // Color palette based on #543A14 (primary brown color)
  const colors = {
    light: {
      primary: {
        main: '#7B592B',
        light: '#A37C44',
        dark: '#543A14',
        contrastText: '#FFFFFF'
      },
      background: {
        default: '#F8F5F0',
        paper: '#FFFFFF'
      },
      text: {
        primary: '#2C2417',
        secondary: '#5F4B2E'
      }
    },
    dark: {
      primary: {
        main: '#8F6A33',
        light: '#B08C55',
        dark: '#543A14',
        contrastText: '#FFFFFF'
      },
      background: {
        default: '#221A0D',
        paper: '#362C1A'
      },
      text: {
        primary: '#E6D6BC',
        secondary: '#B8A689'
      }
    },
    contrast: {
      primary: {
        main: '#A37C44',
        light: '#C9A873',
        dark: '#543A14',
        contrastText: '#FFFFFF'
      },
      background: {
        default: '#121212',
        paper: '#1E1E1E'
      },
      text: {
        primary: '#FFFFFF',
        secondary: '#D4C4A9'
      }
    }
  };

  // Sample code for theme implementation
  const createThemeCode = (mode) => {
    return `
// MUI Theme Configuration for ${mode} mode based on #543A14
// Use this in your createTheme function

const ${mode}ThemeOptions = {
  palette: {
    mode: '${mode === 'light' ? 'light' : 'dark'}',
    primary: {
      main: '${colors[mode].primary.main}',
      light: '${colors[mode].primary.light}',
      dark: '${colors[mode].primary.dark}',
      contrastText: '${colors[mode].primary.contrastText}'
    },
    background: {
      default: '${colors[mode].background.default}',
      paper: '${colors[mode].background.paper}'
    },
    text: {
      primary: '${colors[mode].text.primary}',
      secondary: '${colors[mode].text.secondary}'
    }
  }
};
`;
  };

  return (
    <div className="p-4 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Color Palette for #543A14</h1>
      
      {Object.entries(colors).map(([mode, palette]) => (
        <div key={mode} className="mb-8">
          <h2 className="text-xl font-semibold mb-3 capitalize">{mode} Theme</h2>
          
          <div className="grid grid-cols-4 gap-4 mb-4">
            {Object.entries(palette.primary).map(([variant, color]) => (
              <div key={variant} className="flex flex-col items-center">
                <div 
                  className="w-16 h-16 rounded-md shadow-md mb-1" 
                  style={{ backgroundColor: color }}
                ></div>
                <span className="text-sm font-medium">{variant}</span>
                <span className="text-xs">{color}</span>
              </div>
            ))}
          </div>
          
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="flex flex-col items-center">
              <div 
                className="w-16 h-16 rounded-md shadow-md mb-1" 
                style={{ backgroundColor: palette.background.default }}
              ></div>
              <span className="text-sm font-medium">Bg Default</span>
              <span className="text-xs">{palette.background.default}</span>
            </div>
            <div className="flex flex-col items-center">
              <div 
                className="w-16 h-16 rounded-md shadow-md mb-1" 
                style={{ backgroundColor: palette.background.paper }}
              ></div>
              <span className="text-sm font-medium">Bg Paper</span>
              <span className="text-xs">{palette.background.paper}</span>
            </div>
            <div className="flex flex-col items-center">
              <div 
                className="w-16 h-16 rounded-md shadow-md mb-1 flex items-center justify-center" 
                style={{ backgroundColor: palette.background.paper }}
              >
                <span style={{ color: palette.text.primary }}>Aa</span>
              </div>
              <span className="text-sm font-medium">Text Primary</span>
              <span className="text-xs">{palette.text.primary}</span>
            </div>
            <div className="flex flex-col items-center">
              <div 
                className="w-16 h-16 rounded-md shadow-md mb-1 flex items-center justify-center" 
                style={{ backgroundColor: palette.background.paper }}
              >
                <span style={{ color: palette.text.secondary }}>Aa</span>
              </div>
              <span className="text-sm font-medium">Text Secondary</span>
              <span className="text-xs">{palette.text.secondary}</span>
            </div>
          </div>
          
          <div className="mt-2 bg-gray-50 p-3 rounded-md">
            <div className="font-medium mb-2">Theme Configuration</div>
            <pre className="p-3 bg-gray-100 rounded text-xs overflow-x-auto">
              {createThemeCode(mode)}
            </pre>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ColorPalette;