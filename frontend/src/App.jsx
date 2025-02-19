import { ThemeProvider, createTheme } from '@mui/material'
import ChatInterface from './components/Chat/ChatInterface'

const theme = createTheme({
  palette: {
    primary: {
      main: '#4F46E5',
    },
  },
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <ChatInterface />
    </ThemeProvider>
  )
}

export default App 