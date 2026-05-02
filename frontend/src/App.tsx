import { ChatWindow } from './components/ChatWindow'
import { ErrorBoundary } from './components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <ChatWindow />
    </ErrorBoundary>
  )
}

export default App
