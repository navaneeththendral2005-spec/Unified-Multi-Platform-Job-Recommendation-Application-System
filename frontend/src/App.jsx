import { useState } from 'react'
import LandingPage from './pages/LandingPage'
import AuthPage from './pages/AuthPage'
import AppShell from './pages/AppShell'
import { getToken, clearToken } from './lib/api'
import ClickSpark from './components/ClickSpark'

export default function App() {
  const [view, setView] = useState(getToken() ? 'app' : 'landing')
  return (
    <ClickSpark
      sparkColor="#11130f"
      sparkSize={11}
      sparkRadius={15}
      sparkCount={8}
      duration={400}
    >
      {view === 'auth' && <AuthPage onBack={()=>setView('landing')} onAuthenticated={()=>{ localStorage.removeItem('careerai_resume_filename'); localStorage.removeItem('careerai_saved_jobs'); localStorage.removeItem('careerai_preferences'); setView('app') }} />}
      {view === 'app' && <AppShell onLogout={()=>setView('landing')} />}
      {view === 'landing' && <LandingPage onGetStarted={()=>setView('auth')} />}
    </ClickSpark>
  )
}
