import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2e7d32' },
    secondary: { main: '#00695c' },
  },
  shape: {
    borderRadius: 10,
  },
  typography: {
    fontFamily: 'Roboto, "Segoe UI", sans-serif',
  },
})
