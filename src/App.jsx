import { Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import GraphEditor from './pages/GraphEditor'
import Backtesting from './pages/Backtesting'
import Settings from './pages/Settings'

function App() {
  return (
    <>
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#161b22',
            color: '#c9d1d9',
            border: '1px solid #30363d',
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="editor" element={<GraphEditor />} />
          <Route path="editor/:graphId" element={<GraphEditor />} />
          <Route path="backtesting" element={<Backtesting />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </>
  )
}

export default App
