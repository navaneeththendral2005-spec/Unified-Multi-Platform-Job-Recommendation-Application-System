import { useState } from 'react'
import { ArrowLeft, ArrowRight, BriefcaseBusiness, LockKeyhole, Mail, UserRound } from 'lucide-react'
import Logo from '../components/Logo'
import { api, setToken } from '../lib/api'

export default function AuthPage({ onBack, onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      if (mode === 'register') await api('/auth/register', { method: 'POST', body: JSON.stringify(form) })
      const result = await api('/auth/login', { method: 'POST', body: JSON.stringify({ email: form.email, password: form.password }) })
      setToken(result.access_token); onAuthenticated()
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return <div className="auth-page"><div className="auth-panel"><button className="back-btn" onClick={onBack}><ArrowLeft size={17}/> Back</button><div className="auth-logo"><Logo/></div><div className="auth-copy"><p className="eyebrow">WELCOME TO CAREERAI</p><h1>{mode === 'login' ? 'Your next opportunity starts here.' : 'Build your intelligent career profile.'}</h1><p>{mode === 'login' ? 'Sign in to continue your personalized career journey.' : 'Create your account and let the platform understand what you bring to the market.'}</p></div><form onSubmit={submit}>{mode === 'register' && <label><span>Name</span><div className="input"><UserRound size={17}/><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="Your name"/></div></label>}<label><span>Email</span><div className="input"><Mail size={17}/><input required type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} placeholder="you@example.com"/></div></label><label><span>Password</span><div className="input"><LockKeyhole size={17}/><input required type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder="••••••••"/></div></label>{error && <div className="form-error">{error}</div>}<button className="btn btn-primary btn-large full" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'} <ArrowRight size={18}/></button></form><p className="switch">{mode === 'login' ? 'New to CareerAI?' : 'Already have an account?'} <button onClick={()=>{setMode(mode==='login'?'register':'login');setError('')}}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p></div><div className="auth-art"><div className="art-grid"/><div className="art-ring ring-a"/><div className="art-ring ring-b"/><div className="auth-3d-card"><div className="auth-card-top"><span><BriefcaseBusiness size={17}/> CareerAI</span><b>92%</b></div><h3>Your career,<br/><em>intelligently connected.</em></h3><div className="auth-bars"><span/><span/><span/><span/></div></div></div></div>
}
