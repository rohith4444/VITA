import React from 'react';

const ColorPalette2 = () => {
  // Color palette based on #293D33 (deep forest green)
  const colors = {
    light: {
      primary: {
        main: '#3A574A',
        light: '#5D7D6E',
        dark: '#293D33',
        contrastText: '#FFFFFF'
      },
      background: {
        default: '#F5F8F7',
        paper: '#FFFFFF'
      },
      text: {
        primary: '#1A2922',
        secondary: '#40574C'
      }
    },
    dark: {
      primary: {
        main: '#4A6B5C',
        light: '#6D8E7F',
        dark: '#293D33',
        contrastText: '#FFFFFF'
      },
      background: {
        default: '#141E1A',
        paper: '#1E2C25'
      },
      text: {
        primary: '#D6E5E0',
        secondary: '#A7BDB5'
      }
    },
    contrast: {
      primary: {
        main: '#5D7D6E',
        light: '#8CA99C',
        dark: '#293D33',
        contrastText: '#FFFFFF'
      },
      background: {
        default: '#121212',
        paper: '#1E1E1E'
      },
      text: {
        primary: '#FFFFFF',
        secondary: '#C7DCD5'
      }
    }
  };

  // Sample code for theme implementation
  const createThemeCode = (mode) => {
    return `
// MUI Theme Configuration for ${mode} mode based on #293D33
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
      <h1 className="text-2xl font-bold mb-6">Color Palette for #293D33</h1>
      
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

export default ColorPalette2;