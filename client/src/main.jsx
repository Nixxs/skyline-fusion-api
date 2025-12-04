import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import App from "./App.jsx";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";

const theme = createTheme({
  palette: {
    mode: "light",
    background: {
      default: "#ffffff",
      paper: "#f5f5f5",
    },
    text: {
      default: "#0e1726",
      primary: "#0e1726",
      secondary: "#a0a0a0",
      disabled: "rgba(255,255,255,0.4)"
    }
  },
  components: {
    MuiButton: {
      styleOverrides: {
        contained: {
          fontSize: 14,
          backgroundColor: '#003366',
          color: '#ffffff',
          '&:hover': {
            backgroundColor: '#002244',
          },
          height: 38
        },
        outlined: {
          fontSize: 14,
          color: '#003366',
          borderColor: '#003366',
          '&:hover': {
            borderColor: '#002244',
            backgroundColor: 'rgba(0, 51, 102, 0.04)',
          },
          height: 38
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        size: 'small',        // slimmer by default
        variant: 'outlined',  // optional, if you want this default
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          fontSize: 14,       // smaller font
          '& .MuiInputBase-input': {
            paddingTop: 10,
            paddingBottom: 10, // reduce vertical padding
          },
        },
      },
    },
    // If you also want smaller labels:
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontSize: 14,
        },
      },
    },
    scrollbarWidth: "none",
    "&::-webkit-scrollbar": {
      display: "none"
    }
  },
});

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter basename="drone-image-viewer">
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <App />
        </LocalizationProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>
);
