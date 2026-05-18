import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import MonitorPage from './pages/MonitorPage'
import AnalyticsPage from './pages/AnalyticsPage'
import PerformancePage from './pages/PerformancePage'
import ChatbotPage from './pages/ChatbotPage'
import LoginPage from './pages/LoginPage'

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth()
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return children
}

function App() {
  const { user } = useAuth()
  const location = useLocation()
  
  if (user && location.pathname === '/login') {
    return <Navigate to="/monitor" replace />
  }

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {user && <Navbar />}
      <main className="flex-grow">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><LandingPage /></ProtectedRoute>} />
          <Route path="/monitor" element={<ProtectedRoute><MonitorPage /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><AnalyticsPage /></ProtectedRoute>} />
          <Route path="/performance" element={<ProtectedRoute><PerformancePage /></ProtectedRoute>} />
          <Route path="/chatbot" element={<ProtectedRoute><ChatbotPage /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  )
}


export default App
