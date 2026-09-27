import { useEffect, useMemo, useState } from 'react'
import {
  Bell, BriefcaseBusiness, Check, CheckCircle2, ChevronRight, CircleAlert, Compass, ExternalLink,
  FileText, LayoutDashboard, Link2, LoaderCircle, LogOut, MapPin, RefreshCw,
  Search, Settings, ShieldCheck, SlidersHorizontal, Sparkles, Upload, UserRound, X, Pencil, GraduationCap, Code2
} from 'lucide-react'
import { accountStorageKey, clearToken, endpoints } from '../lib/api'
import Logo from '../components/Logo'

const NAV = [
  ['Dashboard', LayoutDashboard],
  ['Discover Jobs', Compass],
  ['Recommendations', Sparkles],
  ['Applications', FileText],
  ['Resume & Profile', UserRound],
  ['Notifications', Bell],
]

export default function AppShell({ onLogout }) {
  const [page, setPage] = useState('Dashboard')
  const [selectedJob, setSelectedJob] = useState(null)
  const [selectedJobLoading, setSelectedJobLoading] = useState(false)
  const [data, setData] = useState({ me: null, recs: [], jobs: [], applications: [], applicationSummary: null, notifications: [], profile: null, resume: null, sources: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadWorkspace = async () => {
    setLoading(true)
    setError('')
    const results = await Promise.allSettled([
      endpoints.me(),
      endpoints.recommendations(),
      endpoints.jobs(),
      endpoints.applications(),
      endpoints.applicationSummary(),
      endpoints.notifications(true),
      endpoints.profile(),
      endpoints.resume(),
      endpoints.sources(),
    ])

    const [me, recs, jobs, applications, applicationSummary, notifications, profile, resume, sources] = results
    const value = (result, fallback) => result.status === 'fulfilled' ? result.value : fallback
    const profileValue = value(profile, null)
    setData({
      me: value(me, null),
      recs: value(recs, {})?.recommendations || [],
      jobs: value(jobs, []) || [],
      applications: value(applications, {})?.items || [],
      applicationSummary: value(applicationSummary, null),
      notifications: value(notifications, []) || [],
      profile: profileValue,
      resume: value(resume, null),
      sources: value(sources, []) || [],
    })
    if (results.every((result) => result.status === 'rejected')) {
      setError('The workspace could not load its backend data. Check that the API server is running.')
    }
    setLoading(false)
  }

  useEffect(() => { loadWorkspace() }, [])

  const logout = () => {
    // Remove only legacy unscoped browser state. Account-owned data is fetched from the backend.
    localStorage.removeItem('careerai_resume_filename')
    localStorage.removeItem('careerai_saved_jobs')
    localStorage.removeItem('careerai_preferences')
    clearToken()
    onLogout()
  }

  const openJob = async (job) => {
    if (!job?.job_id && !job?.id) return
    setSelectedJobLoading(true)
    setSelectedJob(job)
    setPage('Job Details')
    try {
      const id = job.job_id || job.id
      const details = await endpoints.job(id)
      setSelectedJob({ ...job, ...details })
    } catch {
      // Recommendation payloads already contain enough information to render the detail view.
    } finally {
      setSelectedJobLoading(false)
    }
  }

  const backToRecommendations = () => {
    setSelectedJob(null)
    setPage('Recommendations')
  }

  const unread = data.notifications.length
  const initial = data.me?.name?.[0]?.toUpperCase() || 'U'

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <Logo />
        <nav>
          {NAV.map(([label, Icon]) => (
            <button key={label} className={page === label ? 'selected' : ''} onClick={() => setPage(label)}>
              <Icon size={18} />
              {label}
              {label === 'Notifications' && unread > 0 && <i>{unread}</i>}
            </button>
          ))}
        </nav>
        <div className="side-bottom">
          <button className={page === 'Settings' ? 'selected' : ''} onClick={() => setPage('Settings')}><Settings size={18} />Settings</button>
          <button onClick={logout}><LogOut size={18} />Sign out</button>
        </div>
      </aside>

      <main className="app-main">
        <header className="app-header">
          <div className="mobile-logo"><Logo compact /></div>
          <div className="global-search">
            <Search size={17} />
            <input placeholder="Search jobs, skills, companies..." />
          </div>
          <div className="header-actions">
            <button onClick={() => setPage('Notifications')} aria-label="Notifications"><Bell size={19} />{unread > 0 && <i>{unread}</i>}</button>
            <button className="user-chip" onClick={() => setPage('Resume & Profile')}>
              <div className="avatar">{initial}</div>
              <span>{data.me?.name || 'Your profile'}<small>Career workspace</small></span>
              <ChevronRight size={15} />
            </button>
          </div>
        </header>

        <div className="app-content">
          {page !== 'Job Details' && <div className="app-title">
            <div><p className="eyebrow">CAREER WORKSPACE</p><h1>{page}</h1></div>
            <div className="status-pill"><span /> All systems ready</div>
          </div>}

          {error && <div className="workspace-error"><CircleAlert size={17} />{error}<button onClick={loadWorkspace}><RefreshCw size={14} />Retry</button></div>}
          {loading ? <div className="loading-card"><LoaderCircle className="spin" size={24} /><span>Loading your career intelligence…</span></div> : (
            <>
              {page === 'Dashboard' && <Dashboard data={data} onNavigate={setPage} />}
              {page === 'Discover Jobs' && <JobsPage jobs={data.jobs} recommendations={data.recs} onRefresh={loadWorkspace} onSelect={openJob} />}
              {page === 'Recommendations' && <RecommendationsPage recommendations={data.recs} onSelect={openJob} />}
              {page === 'Job Details' && <JobDetailsPage job={selectedJob} recommendations={data.recs} loading={selectedJobLoading} userId={data.me?.id} onBack={backToRecommendations} onSelect={openJob} />}
              {page === 'Applications' && <ApplicationsPage applications={data.applications} summary={data.applicationSummary} onRefresh={loadWorkspace} />}
              {page === 'Resume & Profile' && <ResumeProfilePage me={data.me} profile={data.profile} resume={data.resume} onRefresh={loadWorkspace} />}
              {page === 'Notifications' && <NotificationsPage notifications={data.notifications} onRefresh={loadWorkspace} />}
              {page === 'Settings' && <SettingsPage sources={data.sources} profile={data.profile} userId={data.me?.id} onRefresh={loadWorkspace} onNavigate={setPage} />}
            </>
          )}
        </div>
      </main>
    </div>
  )
}

function Dashboard({ data, onNavigate }) {
  const recs = data.recs.slice(0, 3)
  const firstName = data.me?.name?.split(' ')[0]
  return <>
    <section className="welcome-card">
      <div>
        <span className="mini-pill"><Sparkles size={13} /> PERSONALIZED FOR YOU</span>
        <h2>Good day{firstName ? `, ${firstName}` : ''}. 👋</h2>
        <p>Your opportunities, applications and career intelligence in one place.</p>
      </div>
      <div className="profile-ring"><b>{data.profile ? '92%' : '—'}</b><small>profile</small></div>
    </section>

    <div className="metric-grid">
      <Metric label="Recommended jobs" value={data.recs.length} />
      <Metric label="Active applications" value={data.applicationSummary?.active ?? 0} />
      <Metric label="Unread updates" value={data.notifications.length} />
      <Metric label="Total applications" value={data.applicationSummary?.total ?? 0} />
    </div>

    <section className="panel">
      <div className="panel-head"><div><p className="eyebrow">AI RECOMMENDATIONS</p><h2>Opportunities that fit you</h2></div><button onClick={() => onNavigate('Recommendations')}>Explore all <ChevronRight size={16} /></button></div>
      {recs.length ? <div className="rec-grid">{recs.map(job => <RecommendationCard key={job.job_id} job={job} />)}</div> : <EmptyState title="No recommendations yet" text="Complete your profile and upload a resume to unlock personalized opportunities." />}
    </section>
  </>
}

function Metric({ label, value }) { return <div className="metric"><span>{label}</span><b>{value}</b><small>Live from your workspace</small></div> }

function RecommendationCard({ job }) {
  return <article className="rec-card">
    <div className="rec-top"><div className="company-logo">{job.company?.[0] || 'C'}</div><span>{job.match_score}% match</span></div>
    <h3>{job.title}</h3><p>{job.company} · {job.location || 'Location flexible'}</p>
    <div className="tag-row">{(job.matched_skills || []).slice(0, 4).map(skill => <i key={skill}>{skill}</i>)}</div>
    <div className="rec-foot"><span>{job.match_level || 'Matched'}</span><span>{job.skill_match_percentage ?? 0}% skills</span></div>
  </article>
}

function JobsPage({ jobs, recommendations, onRefresh, onSelect }) {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(null)
  const filtered = useMemo(() => jobs.filter(job => {
    const text = `${job.title} ${job.company} ${job.location || ''} ${job.required_skills || ''}`.toLowerCase()
    return text.includes(query.toLowerCase())
  }), [jobs, query])

  return <section className="workspace-section">
    <div className="toolbar panel">
      <div className="inline-search"><Search size={17} /><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search title, company, skill or location" /></div>
      <button className="btn btn-soft" onClick={onRefresh}><RefreshCw size={15} /> Refresh</button>
    </div>
    <div className="section-meta"><span>{filtered.length} jobs available</span><span>{recommendations.length} personalized matches</span></div>
    {filtered.length ? <div className="job-list">{filtered.map(job => <JobCard key={job.id} job={job} onSelect={onSelect} />)}</div> : <EmptyState title="No jobs found" text={jobs.length ? 'Try a different search term.' : 'No jobs are currently available in the connected catalog.'} />}

  </section>
}

function JobCard({ job, onSelect }) {
  return <article className="job-card job-card-clickable" onClick={() => onSelect(job)}>
    <div className="company-logo large">{job.company?.[0] || 'C'}</div>
    <div className="job-main"><div className="job-heading"><div><h3>{job.title}</h3><p>{job.company}</p></div><span>{job.job_type || 'Role'}</span></div><p className="job-location"><MapPin size={13} /> {job.location || 'Location flexible'} · {job.experience_required || 'Experience varies'}</p><p className="job-description">{job.description}</p><div className="job-tags">{(job.required_skills || '').split(',').map(s => s.trim()).filter(Boolean).slice(0, 5).map(s => <i key={s}>{s}</i>)}</div></div>
    <button className="icon-btn" onClick={event => { event.stopPropagation(); onSelect(job) }} aria-label="View job"><ChevronRight /></button>
  </article>
}

function JobModal({ job, onClose }) {
  return <div className="modal-backdrop" onMouseDown={onClose}><div className="modal-card" onMouseDown={e => e.stopPropagation()}>
    <button className="modal-close" onClick={onClose}><X /></button>
    <div className="company-logo large">{job.company?.[0] || 'C'}</div><p className="eyebrow">JOB OPPORTUNITY</p><h2>{job.title}</h2><p className="modal-subtitle">{job.company} · {job.location || 'Location flexible'}</p>
    <div className="detail-grid"><Detail label="Job type" value={job.job_type || 'Not specified'} /><Detail label="Experience" value={job.experience_required || 'Not specified'} /><Detail label="Skills" value={job.required_skills || 'Not specified'} /></div>
    <div className="modal-description">{job.description}</div>
    <div className="modal-actions">{job.application_link ? <a className="btn btn-primary" href={job.application_link} target="_blank" rel="noreferrer">Apply at source <ExternalLink size={15} /></a> : <span className="muted-note">No external application link is available for this listing.</span>}</div>
  </div></div>
}

function RecommendationsPage({ recommendations, onSelect }) {
  return <section className="workspace-section">
    <div className="recommendation-intro">
      <div><span className="eyebrow">PERSONALIZED MATCHES</span><h2>Opportunities selected for your profile</h2><p>Each match is scored from your skills, experience, preferences and the job requirements.</p></div>
      <div className="recommendation-count"><b>{recommendations.length}</b><span>personalized jobs</span></div>
    </div>
    {recommendations.length ? <div className="recommendation-list">{recommendations.map(job => <RecommendationRow key={job.job_id} job={job} onSelect={onSelect} />)}</div> : <EmptyState title="Your recommendations will appear here" text="Complete your profile and upload a resume to unlock personalized opportunities." />}
  </section>
}

function RecommendationRow({ job, onSelect }) {
  const score = Number(job.match_score || 0)
  return <button className="recommendation-row recommendation-clickable" onClick={() => onSelect(job)}>
    <div className="company-logo large">{job.company?.[0] || 'C'}</div>
    <div className="recommendation-main">
      <div className="recommendation-heading"><div><span className="recommended-badge">Recommended</span><h3>{job.title}</h3><p>{job.company} · {job.location || 'Location flexible'}</p></div><div className="recommendation-score"><strong>{score}%</strong><span>match</span></div></div>
      <div className="recommendation-meta"><span><MapPin size={13} />{job.location || 'Location flexible'}</span><span><BriefcaseBusiness size={13} />{job.job_type || 'Full-time'}</span><span>{job.experience_required || 'Experience varies'}</span></div>
      <div className="match-bar"><span style={{ width: `${Math.min(100, Math.max(0, score))}%` }} /></div>
      <p className="recommendation-summary">{(job.reasons || [])[0] || 'Strong alignment with your current career profile and job requirements.'}</p>
      <div className="job-tags">{(job.matched_skills || []).slice(0, 5).map(skill => <i key={skill}>{skill}</i>)}{(job.matched_skills || []).length > 5 && <i>+{job.matched_skills.length - 5}</i>}</div>
    </div>
    <span className="recommendation-arrow"><ChevronRight size={20} /></span>
  </button>
}

function JobDetailsPage({ job, recommendations, loading, userId, onBack, onSelect }) {
  const [activeTab, setActiveTab] = useState('Overview')
  const [applying, setApplying] = useState(false)
  const [applyMessage, setApplyMessage] = useState('')
  const [saved, setSaved] = useState(false)
  useEffect(() => {
    if (!job) return
    try { setSaved(JSON.parse(localStorage.getItem(accountStorageKey('saved_jobs', userId)) || '[]').includes(job.id || job.job_id)) } catch {}
    setApplyMessage('')
    setActiveTab('Overview')
  }, [job?.id, job?.job_id])

  if (!job) return <div className="job-details-loading"><LoaderCircle className="spin" size={24} />Preparing job details…</div>
  const score = Number(job.match_score || 0)
  const reasons = job.reasons || []
  const required = splitSkills(job.required_skills)
  const matched = job.matched_skills || []
  const missing = job.missing_skills || []
  const similar = recommendations.filter(item => item.job_id !== (job.id || job.job_id)).slice(0, 3)
  const apply = async () => {
    const applicationLink = getSafeApplicationLink(job.application_link)
    setApplying(true)
    setApplyMessage('')

    // Only open a tab when the source URL is a real HTTP(S) application link.
    // Placeholder domains such as example.com are deliberately treated as
    // missing links so users are never sent to a useless blank/example page.
    const sourceWindow = applicationLink
      ? window.open(applicationLink, '_blank', 'noopener,noreferrer')
      : null

    try {
      // The application record is created even when the listing has no usable
      // external URL. The backend accepts a nullable application_url.
      await endpoints.createApplication({
        job_id: job.id || job.job_id,
        source_platform: 'connected_job_source',
        application_url: applicationLink,
      })

      if (applicationLink) {
        setApplyMessage('Application saved to your CareerAI tracker. The original application page is opening now.')
      } else {
        setApplyMessage('Application saved to your CareerAI tracker. This listing does not currently provide an authorized application link.')
      }
    } catch (error) {
      if (/already applied/i.test(error.message)) {
        setApplyMessage(
          applicationLink
            ? 'You already have this job in your application tracker. The original application page is open.'
            : 'You already have this job in your application tracker. No authorized application link is available for this listing.'
        )
      } else {
        setApplyMessage(`We could not save the application yet: ${error.message}`)
      }
    } finally {
      setApplying(false)
      // If a real source URL exists but the browser blocked the popup, try the
      // normal navigation API as a fallback. Never open a blank/placeholder tab.
      if (applicationLink && !sourceWindow) {
        window.open(applicationLink, '_blank', 'noopener,noreferrer')
      }
    }
  }
  const toggleSaved = () => {
    const id = job.id || job.job_id
    try {
      const current = JSON.parse(localStorage.getItem(accountStorageKey('saved_jobs', userId)) || '[]')
      const next = saved ? current.filter(item => item !== id) : [...new Set([...current, id])]
      localStorage.setItem(accountStorageKey('saved_jobs', userId), JSON.stringify(next)); setSaved(!saved)
    } catch {}
  }
  return <section className="job-details-page">
    <div className="job-breadcrumb"><button onClick={onBack}><ChevronRight size={15} className="breadcrumb-back-icon" /> Recommendations</button><span>›</span><span>{job.title}</span><div className="job-nav-actions"><button onClick={onBack}>← Back to recommendations</button></div></div>
    <div className="job-hero-card">
      <div className="job-hero-main"><div className="company-logo hero-logo">{job.company?.[0] || 'C'}</div><div><div className="hero-eyebrow">RECOMMENDED OPPORTUNITY</div><h2>{job.title}</h2><p className="hero-company">{job.company} <ExternalLink size={14} /></p><p className="hero-company-note">Opportunity presented with source attribution so you can review the original listing context before applying.</p></div></div>
      <div className="job-hero-actions"><div className="match-score-card"><strong>{score}%</strong><span>Match Score</span></div><button className="apply-btn" onClick={apply} disabled={applying}>{applying ? 'Saving…' : 'Apply Now'} <ExternalLink size={15} /></button><button className={`save-btn ${saved ? 'saved' : ''}`} onClick={toggleSaved}>{saved ? 'Saved' : 'Save Job'}</button></div>
      <div className="job-meta-strip"><span><MapPin size={16} />{job.location || 'Location flexible'}</span><span><BriefcaseBusiness size={16} />{job.job_type || 'Full-time'}</span><span><UserRound size={16} />{job.experience_required || 'Experience varies'}</span><span><Link2 size={16} />Connected job source</span>{job.created_at && <span><FileText size={16} />Posted {formatDate(job.created_at)}</span>}</div>
    </div>
    {applyMessage && <div className={`apply-message ${applyMessage.includes('could not') ? 'warning' : 'success'}`}><Check size={16} />{applyMessage}</div>}
    <div className="job-tabs">{['Overview','About Company','Skills & Requirements','Similar Jobs'].map(tab => <button key={tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab}</button>)}</div>
    {activeTab === 'Overview' && <div className="job-detail-grid"><div className="job-detail-main"><DetailSection icon={<Sparkles size={19} />} title="Why this job matches you"><div className="match-reasons">{reasons.length ? reasons.map((reason, index) => <div key={reason}><Check size={16} />{reason}</div>) : <div><Check size={16} />This opportunity aligns with your current candidate profile.</div>}{matched.length > 0 && <div><Check size={16} />Matched skills: {matched.join(', ')}</div>}{missing.length > 0 && <div className="skill-gap"><CircleAlert size={16} />Skill gaps: {missing.join(', ')}</div>}</div></DetailSection><DetailSection icon={<FileText size={19} />} title="Job description"><p className="detail-copy">{job.description || 'No detailed description was provided by the source.'}</p></DetailSection><DetailSection icon={<Settings size={19} />} title="Key requirements"><div className="requirements-columns"><div><h4>Required skills</h4><div className="skill-cloud">{(required.length ? required : matched).map(skill => <span key={skill}>{skill}</span>)}</div></div><div><h4>Preferred / matched skills</h4><div className="skill-cloud preferred">{matched.length ? matched.map(skill => <span key={skill}>{skill}</span>) : <span>Based on profile match</span>}</div></div></div></DetailSection></div><aside className="job-detail-side"><DetailSection icon={<BriefcaseBusiness size={18} />} title="At a glance"><div className="glance-list"><Detail label="Job type" value={job.job_type || 'Not specified'} /><Detail label="Experience" value={job.experience_required || 'Not specified'} /><Detail label="Location" value={job.location || 'Not specified'} /><Detail label="Source" value="Connected job source" /></div></DetailSection><div className="source-card-highlight"><Link2 size={21} /><div><h4>Source attribution</h4><p>This opportunity keeps its original source context. Review the source listing before applying.</p></div></div></aside></div>}
    {activeTab === 'About Company' && <div className="single-detail-panel"><DetailSection icon={<BriefcaseBusiness size={19} />} title={job.company || 'Company'}><p className="detail-copy">Company information is presented from the connected job listing. CareerAI does not invent company facts that were not supplied by the source.</p><div className="company-fact-grid"><Detail label="Company" value={job.company || 'Not specified'} /><Detail label="Location" value={job.location || 'Not specified'} /><Detail label="Source" value="Connected job source" /></div></DetailSection></div>}
    {activeTab === 'Skills & Requirements' && <div className="single-detail-panel"><DetailSection icon={<Settings size={19} />} title="Skills & requirements"><div className="requirements-columns"><div><h4>Required</h4><div className="skill-cloud">{(required.length ? required : matched).map(skill => <span key={skill}>{skill}</span>)}</div></div><div><h4>Profile gaps</h4><div className="skill-cloud gaps">{missing.length ? missing.map(skill => <span key={skill}>{skill}</span>) : <span>No significant gaps reported</span>}</div></div></div></DetailSection></div>}
    {activeTab === 'Similar Jobs' && <div className="similar-job-grid">{similar.length ? similar.map(item => <button key={item.job_id} className="similar-job-card" onClick={() => onSelect(item)}><div className="company-logo">{item.company?.[0] || 'C'}</div><div><h3>{item.title}</h3><p>{item.company} · {item.location || 'Location flexible'}</p><strong>{item.match_score}% match</strong></div><ChevronRight size={18} /></button>) : <EmptyState title="No similar jobs available" text="More opportunities will appear here as the connected job catalog grows." />}</div>}
    {loading && <div className="detail-loading-overlay"><LoaderCircle className="spin" size={22} />Loading latest job details…</div>}
  </section>
}

function DetailSection({ icon, title, children }) { return <section className="detail-section"><div className="detail-section-title"><span>{icon}</span><h3>{title}</h3></div>{children}</section> }
function splitSkills(value) { return String(value || '').split(',').map(item => item.trim()).filter(Boolean) }

function getSafeApplicationLink(value) {
  if (!value || typeof value !== 'string') return null
  try {
    const url = new URL(value, window.location.origin)
    if (!['http:', 'https:'].includes(url.protocol)) return null

    const hostname = url.hostname.toLowerCase()
    const placeholderHosts = ['example.com', 'example.org', 'example.net']
    if (placeholderHosts.some(host => hostname === host || hostname.endsWith(`.${host}`))) return null

    return url.href
  } catch {
    return null
  }
}



function ApplicationsPage({ applications, summary, onRefresh }) {
  const [selected, setSelected] = useState(null)
  const [status, setStatus] = useState('')
  const [saving, setSaving] = useState(false)
  const [lifecycle, setLifecycle] = useState([])
  useEffect(() => { endpoints.applicationLifecycle().then(setLifecycle).catch(() => setLifecycle([])) }, [])

  const updateStatus = async () => {
    if (!selected || !status) return
    setSaving(true)
    try { await endpoints.updateApplicationStatus(selected.id, { status }); setSelected(null); await onRefresh() } catch (error) { alert(error.message) } finally { setSaving(false) }
  }

  return <section className="workspace-section">
    <div className="metric-grid application-metrics"><Metric label="Total" value={summary?.total ?? applications.length} /><Metric label="Active" value={summary?.active ?? 0} /><Metric label="Terminal" value={summary?.terminal ?? 0} /><Metric label="Current page" value={applications.length} /></div>
    <div className="panel"><div className="panel-head"><div><p className="eyebrow">APPLICATION TRACKER</p><h2>Your applications</h2></div><button onClick={onRefresh}><RefreshCw size={15} /></button></div>{applications.length ? <div className="application-list">{applications.map(app => <article className="application-row" key={app.id}><div className="company-logo">{app.job?.company?.[0] || 'C'}</div><div className="application-main"><h3>{app.job?.title}</h3><p>{app.job?.company} · {app.job?.location || 'Location flexible'}</p><small>Applied {formatDate(app.applied_at)}</small></div><span className={`status-badge status-${slug(app.status)}`}>{app.status}</span><button className="btn btn-soft small-btn" onClick={() => { setSelected(app); setStatus(app.status) }}>Update</button></article>)}</div> : <EmptyState title="No applications yet" text="When you apply to a job through a connected workflow, it can be tracked here." />}</div>
    {selected && <div className="modal-backdrop" onMouseDown={() => setSelected(null)}><div className="modal-card small-modal" onMouseDown={e => e.stopPropagation()}><button className="modal-close" onClick={() => setSelected(null)}><X /></button><p className="eyebrow">APPLICATION STATUS</p><h2>{selected.job?.title}</h2><p className="modal-subtitle">{selected.job?.company}</p><label className="form-field">Status<select value={status} onChange={e => setStatus(e.target.value)}>{(lifecycle.find(item => item.status === selected.status)?.allowed_next_statuses || [selected.status]).map(item => <option key={item} value={item}>{formatStatus(item)}</option>)}</select></label><label className="form-field">Notes<textarea defaultValue={selected.notes || ''} disabled placeholder="Status notes can be managed through the application workflow." /></label><button className="btn btn-primary full" disabled={saving} onClick={updateStatus}>{saving ? 'Saving…' : 'Save status'}</button></div></div>}
  </section>
}

function ResumeProfilePage({ me, profile, resume, onRefresh }) {
  const [file, setFile] = useState(null)
  const [fileName, setFileName] = useState(resume?.file_name || '')
  const [analysis, setAnalysis] = useState(null)

  useEffect(() => {
    setFileName(resume?.file_name || '')
    if (!resume?.file_name) {
      setFile(null)
      setAnalysis(null)
    }
  }, [resume?.resume_id, resume?.file_name])
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ skills: profile?.skills || '', experience_years: profile?.experience_years ?? '', education: profile?.education || '', preferred_job_role: profile?.preferred_job_role || '', preferred_location: profile?.preferred_location || '' })

  useEffect(() => {
    setForm({ skills: profile?.skills || '', experience_years: profile?.experience_years ?? '', education: profile?.education || '', preferred_job_role: profile?.preferred_job_role || '', preferred_location: profile?.preferred_location || '' })
  }, [profile])

  const upload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const result = await endpoints.resumeUpload(file)
      const displayName = result?.original_file_name || file.name
      setFileName(displayName)
      setAnalysis(result)
      await onRefresh()
    } catch (error) {
      alert(error.message)
    } finally {
      setUploading(false)
    }
  }

  const save = async e => {
    e.preventDefault(); setSaving(true)
    const payload = { ...form, experience_years: form.experience_years === '' ? null : Number(form.experience_years) }
    try {
      if (profile) await endpoints.updateProfile(payload)
      else await endpoints.createProfile(payload)
      setEditing(false)
      await onRefresh()
    } catch (error) { alert(error.message) } finally { setSaving(false) }
  }

  const skills = splitSkills(form.skills)
  const analyzed = Boolean(analysis?.analysis)
  const displayExperience = form.experience_years === '' || form.experience_years === null ? 'Not specified' : `${form.experience_years} ${Number(form.experience_years) === 1 ? 'year' : 'years'}`
  const profileRows = [
    { icon: <UserRound size={17} />, label: 'Full name', value: me?.name || 'Not specified' },
    { icon: <BriefcaseBusiness size={17} />, label: 'Professional title', value: form.preferred_job_role || 'Not specified' },
    { icon: <BriefcaseBusiness size={17} />, label: 'Experience', value: displayExperience },
    { icon: <GraduationCap size={17} />, label: 'Education', value: form.education || 'Not specified' },
    { icon: <MapPin size={17} />, label: 'Location', value: form.preferred_location || 'Not specified' },
  ]

  return <section className="resume-profile-page">
    <p className="resume-page-subtitle">Upload your resume to extract key details and keep your profile updated.</p>
    <div className="resume-profile-grid">
      <div className="panel resume-analysis-panel">
        <div className="resume-panel-head">
          <div className="resume-icon gold"><FileText size={20} /></div>
          <div><h2>Resume analysis</h2><p>Upload your resume to extract and update your profile details.</p></div>
        </div>
        <label className="resume-dropzone">
          <Upload size={28} />
          <strong>Drag & drop your resume here</strong>
          <span>PDF or DOCX, up to 10 MB</span>
          <span className="resume-browse">Browse files</span>
          <input type="file" accept=".pdf,.docx" onChange={e => setFile(e.target.files?.[0] || null)} />
        </label>
        <div className="resume-file-row">
          <div className="resume-file-info">
            <div className="resume-file-icon"><FileText size={17} /></div>
            <div><b>{file?.name || fileName || 'No resume selected'}</b><small>{file ? `${(file.size / (1024 * 1024)).toFixed(1)} MB` : fileName ? 'Resume analyzed' : 'Choose a PDF or DOCX file'}</small></div>
          </div>
          <button type="button" className="btn btn-primary resume-analyze-btn" disabled={!file || uploading} onClick={upload}><Sparkles size={15} />{uploading ? 'Analyzing…' : 'Analyze resume'}</button>
        </div>
        {analysis?.analysis && <div className="resume-success"><CheckCircle2 size={20} /><div><b>Resume analyzed successfully!</b><span>Your profile details are ready to use.</span></div></div>}
      </div>

      <form className="panel resume-profile-panel" onSubmit={save}>
        <div className="resume-profile-head">
          <div className="resume-icon purple"><UserRound size={20} /></div>
          <div><h2>Your profile</h2><p>Key details extracted from your resume. You can edit them anytime.</p></div>
          <button type="button" className="settings-outline-btn resume-edit-btn" onClick={() => setEditing(value => !value)}><Pencil size={14} />{editing ? 'Close' : 'Edit profile'}</button>
        </div>
        {!editing ? <div className="resume-detail-list">
          {profileRows.map(row => <div className="resume-detail-row" key={row.label}><span className="resume-detail-icon">{row.icon}</span><span className="resume-detail-label">{row.label}</span><strong>{row.value}</strong><ChevronRight size={15} /></div>)}
          <div className="resume-detail-row skills-row"><span className="resume-detail-icon"><Code2 size={17} /></span><span className="resume-detail-label">Key skills</span><div className="resume-skill-list">{skills.length ? skills.slice(0, 6).map(skill => <span key={skill}>{skill}</span>) : <em>No skills added</em>}{skills.length > 6 && <span>+{skills.length - 6}</span>}</div><ChevronRight size={15} /></div>
        </div> : <div className="resume-edit-fields">
          <Field label="Skills" value={form.skills} onChange={v => setForm({ ...form, skills: v })} placeholder="Python, FastAPI, SQL" />
          <Field label="Experience (years)" type="number" value={form.experience_years} onChange={v => setForm({ ...form, experience_years: v })} />
          <Field label="Education" value={form.education} onChange={v => setForm({ ...form, education: v })} placeholder="B.Tech in Computer Science" />
          <Field label="Preferred role" value={form.preferred_job_role} onChange={v => setForm({ ...form, preferred_job_role: v })} placeholder="Backend Developer" />
          <Field label="Preferred location" value={form.preferred_location} onChange={v => setForm({ ...form, preferred_location: v })} placeholder="Chennai" />
          <button className="btn btn-primary full" disabled={saving}>{saving ? 'Saving…' : 'Save profile'}</button>
        </div>}
      </form>
    </div>
  </section>
}

function NotificationsPage({ notifications, onRefresh }) {
  const [busy, setBusy] = useState(null)
  const markRead = async id => { setBusy(id); try { await endpoints.markNotificationRead(id); await onRefresh() } catch (error) { alert(error.message) } finally { setBusy(null) } }
  return <section className="workspace-section"><div className="section-meta"><span>{notifications.length} unread notifications</span><span>Application and career updates</span></div><div className="notification-list">{notifications.length ? notifications.map(note => <article className="notification-row" key={note.id}><div className="notification-icon"><Bell size={17} /></div><div><h3>{note.subject || note.notification_type}</h3><p>{note.body}</p><small>{formatDate(note.created_at)} · {note.channel}</small></div><button className="btn btn-soft small-btn" disabled={busy === note.id} onClick={() => markRead(note.id)}>{busy === note.id ? '…' : 'Mark read'}</button></article>) : <EmptyState title="You're all caught up" text="New application and career updates will appear here." />}</div></section>
}

function ProviderLogo({ provider, label }) {
  const common = { width: 28, height: 28, viewBox: '0 0 28 28', 'aria-hidden': true }
  if (provider === 'linkedin') return <svg {...common} className="provider-brand-svg linkedin"><rect x="2" y="2" width="24" height="24" rx="5" fill="currentColor"/><text x="7" y="20" fill="#fff" fontSize="15" fontWeight="800" fontFamily="Arial, sans-serif">in</text></svg>
  if (provider === 'naukri') return <svg {...common} className="provider-brand-svg naukri"><path d="M6 6h16v4H10v3h9v4h-9v5H6z" fill="currentColor"/><circle cx="21" cy="8" r="2" fill="#fff"/></svg>
  if (provider === 'internshala') return <svg {...common} className="provider-brand-svg internshala"><rect x="3" y="3" width="22" height="22" rx="6" fill="currentColor"/><text x="6" y="19" fill="#fff" fontSize="11" fontWeight="800" fontFamily="Arial, sans-serif">IS</text></svg>
  if (provider === 'indeed') return <svg {...common} className="provider-brand-svg indeed"><circle cx="14" cy="14" r="12" fill="currentColor"/><text x="10" y="20" fill="#fff" fontSize="18" fontWeight="800" fontFamily="Arial, sans-serif">i</text></svg>
  if (provider === 'wellfound') return <svg {...common} className="provider-brand-svg wellfound"><path d="M14 2l2.8 8.2L25 13l-8.2 2.8L14 24l-2.8-8.2L3 13l8.2-2.8z" fill="currentColor"/><circle cx="14" cy="13" r="2.2" fill="#fff"/></svg>
  return <span className="provider-fallback-mark">{label?.[0] || 'J'}</span>
}

function SettingsPage({ sources, profile, userId, onRefresh, onNavigate }) {
  const defaultRoles = profile?.preferred_job_role ? profile.preferred_job_role.split(',').map(v => v.trim()).filter(Boolean) : []
  const defaultLocations = profile?.preferred_location ? profile.preferred_location.split(',').map(v => v.trim()).filter(Boolean) : []
  const [preferences, setPreferences] = useState(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(accountStorageKey('preferences', userId)) || 'null')
      return stored || {
        roles: defaultRoles,
        locations: defaultLocations,
        experience: profile?.experience_years != null ? `${profile.experience_years} years` : '0–2 years',
        remote: true,
        relocate: false,
        skillMatch: true,
        preferredLocation: true,
        experienceLevel: true,
        internships: true,
        startups: true,
        matchingJobs: true,
        applicationUpdates: true,
        interviewReminders: true,
        weeklySummary: true,
        productUpdates: false,
      }
    } catch {
      return { roles: defaultRoles, locations: defaultLocations, experience: '0–2 years', remote: true, relocate: false, skillMatch: true, preferredLocation: true, experienceLevel: true, internships: true, startups: true, matchingJobs: true, applicationUpdates: true, interviewReminders: true, weeklySummary: true, productUpdates: false }
    }
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [systemReady, setSystemReady] = useState(null)
  const [checkingSystem, setCheckingSystem] = useState(false)
  const [connecting, setConnecting] = useState('')

  useEffect(() => {
    if (!localStorage.getItem(accountStorageKey('preferences', userId)) && profile) {
      setPreferences(prev => ({ ...prev, roles: defaultRoles, locations: defaultLocations, experience: profile.experience_years != null ? `${profile.experience_years} years` : prev.experience }))
    }
  }, [profile])

  const update = (key, value) => setPreferences(prev => ({ ...prev, [key]: value }))
  const addChip = (key, value) => {
    const clean = value.trim()
    if (!clean) return
    setPreferences(prev => ({ ...prev, [key]: [...new Set([...(prev[key] || []), clean])] }))
  }
  const removeChip = (key, value) => setPreferences(prev => ({ ...prev, [key]: (prev[key] || []).filter(item => item !== value) }))

  const savePreferences = async () => {
    setSaving(true); setSaved(false)
    try {
      localStorage.setItem(accountStorageKey('preferences', userId), JSON.stringify(preferences))
      const years = preferences.experience.match(/\d+/)?.[0]
      await endpoints.savePreferences({
        preferred_roles: preferences.roles,
        preferred_locations: preferences.locations,
        willing_to_relocate: preferences.relocate,
        experience_level: preferences.experience,
      })
      if (profile) {
        await endpoints.updateProfile({
          preferred_job_role: preferences.roles.join(', '),
          preferred_location: preferences.locations.join(', '),
          experience_years: years ? Number(years) : null,
        }).catch(() => {})
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 2600)
    } catch (error) {
      localStorage.setItem(accountStorageKey('preferences', userId), JSON.stringify(preferences))
      alert(`Preferences saved locally. Backend sync was unavailable: ${error.message}`)
    } finally { setSaving(false) }
  }

  const checkSystem = async () => {
    setCheckingSystem(true)
    try {
      const result = await endpoints.systemReadiness()
      setSystemReady(result)
    } catch {
      try { await endpoints.health(); setSystemReady({ ready: true }) } catch { setSystemReady({ ready: false }) }
    } finally { setCheckingSystem(false) }
  }
  useEffect(() => { checkSystem() }, [])

  const providerCopy = {
    linkedin: "Connect through CareerAI's authorized LinkedIn OAuth flow.",
    naukri: 'Open the official Naukri platform for available integration access.',
    internshala: 'Open the official Internshala platform for available integration access.',
    indeed: "Open Indeed's official developer documentation and integration resources.",
    wellfound: 'Open the official Wellfound platform and integration resources.',
  }

  // Only LinkedIn has a live OAuth flow in our backend today. For the other
  // providers we intentionally send the user to the provider's official
  // access/integration surface rather than inventing an unsupported API flow.
  const providerLinks = {
    naukri: { url: 'https://www.naukri.com/', label: 'Open Naukri' },
    internshala: { url: 'https://internshala.com/', label: 'Open Internshala' },
    indeed: { url: 'https://docs.indeed.com/', label: 'Open developer docs' },
    wellfound: { url: 'https://wellfound.com/', label: 'Open Wellfound' },
  }

  const connectProvider = async (key) => {
    if (key === 'linkedin') {
      setConnecting('linkedin')
      try {
        const result = await endpoints.linkedinConnect()
        if (result?.authorization_url) {
          window.location.assign(result.authorization_url)
        }
      } catch (error) {
        // If local OAuth credentials are not configured yet, still give the
        // user a useful official developer destination instead of a dead button.
        window.open('https://developer.linkedin.com/product-catalog', '_blank', 'noopener,noreferrer')
      } finally { setConnecting('') }
      return
    }

    const target = providerLinks[key]
    if (target?.url) window.open(target.url, '_blank', 'noopener,noreferrer')
  }

  const providerLogo = (key, name) => <ProviderLogo provider={key} label={name} />

  const sourceCards = sources.length ? sources : [
    { name: 'linkedin', display_name: 'LinkedIn', search_supported: false, direct_apply_supported: false, application_status_sync_supported: false, authentication: { authorized: false, status: 'AUTHORIZATION_REQUIRED' } },
    { name: 'naukri', display_name: 'Naukri', authentication: { authorized: false, status: 'AUTHORIZATION_REQUIRED' } },
    { name: 'internshala', display_name: 'Internshala', authentication: { authorized: false, status: 'AUTHORIZATION_REQUIRED' } },
    { name: 'indeed', display_name: 'Indeed', authentication: { authorized: false, status: 'AUTHORIZATION_REQUIRED' } },
    { name: 'wellfound', display_name: 'Wellfound', authentication: { authorized: false, status: 'AUTHORIZATION_REQUIRED' } },
  ]

  const authorizedCount = sourceCards.filter(source => source.authentication?.authorized).length
  const profileItems = [
    ['Resume', Boolean(profile), profile ? 'Uploaded / analyzed' : 'Add your resume'],
    ['Skills', Boolean(profile?.skills), profile?.skills ? `${splitSkills(profile.skills).length} skills` : 'Add skills'],
    ['Experience', profile?.experience_years != null, profile?.experience_years != null ? `${profile.experience_years} years` : 'Add experience'],
    ['Education', Boolean(profile?.education), profile?.education ? 'Added' : 'Add education'],
    ['Career interests', preferences.roles.length > 0, preferences.roles.length ? 'Set' : 'Set preferred roles'],
    ['Preferences', preferences.locations.length > 0, preferences.locations.length ? 'Set' : 'Set locations'],
  ]
  const completed = profileItems.filter(item => item[1]).length
  const completeness = Math.round((completed / profileItems.length) * 100)

  return <section className="settings-workspace">
    <div className="settings-intro"><p>Manage your career connections, preferences and the way CareerAI works for you.</p></div>

    <div className="settings-top-grid">
      <section className="settings-panel integrations-panel">
        <div className="settings-panel-head"><div><div className="settings-icon blue"><Link2 size={19} /></div><div><h3>Connected Job Platforms</h3><p>Manage authorized sources and see exactly what CareerAI can use from each platform.</p></div></div><button className="settings-outline-btn" onClick={onRefresh}><RefreshCw size={14} /> Refresh status</button></div>
        <div className="provider-list">{sourceCards.map(source => {
          const key = source.name?.toLowerCase()
          const authorized = Boolean(source.authentication?.authorized)
          const statusText = authorized ? 'Connected' : 'Needs connection'
          return <article className="provider-card" key={source.name}>
            <div className="provider-logo">{providerLogo(key, source.display_name || source.name)}</div>
            <div className="provider-main"><div className="provider-title-row"><div><h4>{source.display_name || source.name}</h4><p>{providerCopy[key] || 'Career source integration.'}</p></div><span className={`provider-status ${authorized ? 'connected' : 'pending'}`}><span />{statusText}</span></div><div className="provider-capabilities"><span className={source.search_supported ? 'on' : ''}>{source.search_supported ? '✓ Job discovery' : '— Job discovery'}</span><span className={source.direct_apply_supported ? 'on' : ''}>{source.direct_apply_supported ? '✓ External apply' : '— External apply'}</span><span className={source.application_status_sync_supported ? 'on' : ''}>{source.application_status_sync_supported ? '✓ Application tracking' : '— Application tracking'}</span></div></div>
            <div className="provider-action"><button className="settings-action-btn" onClick={() => connectProvider(key)} disabled={connecting === 'linkedin' && key === 'linkedin'}>{connecting === 'linkedin' && key === 'linkedin' ? 'Opening…' : authorized ? 'Manage' : key === 'linkedin' ? 'Connect' : 'Open'} <ExternalLink size={14} /></button></div>
          </article>
        })}</div>
        <div className="integration-note"><ShieldCheck size={17} /><p>CareerAI preserves source attribution and only activates provider capabilities when the required official authorization is available.</p><b>{authorizedCount}/{sourceCards.length} connected</b></div>
      </section>

      <div className="settings-right-stack">
        <section className="settings-panel profile-summary-panel">
          <div className="settings-panel-head compact"><div><div className="settings-icon purple"><UserRound size={19} /></div><div><h3>Your Career Profile</h3><p>Complete your profile to improve recommendation quality.</p></div></div><button className="settings-outline-btn" onClick={onRefresh}><UserRound size={14} /> Refresh</button></div>
          <div className="profile-summary-body"><div className="profile-progress"><div className="profile-progress-ring" style={{ '--progress': `${completeness * 3.6}deg` }}><div><strong>{completeness}%</strong><span>complete</span></div></div></div><div className="profile-checklist">{profileItems.map(([label, done, detail]) => <div key={label}><CheckCircle2 size={16} className={done ? 'done' : ''} /><span><b>{label}</b><small>{detail}</small></span></div>)}</div></div>
          <div className="profile-complete-banner"><Sparkles size={18} /><div><b>Make your recommendations smarter</b><p>Add missing profile details for more accurate matching.</p></div><button onClick={() => onNavigate('Resume & Profile')}>View Profile <ChevronRight size={15} /></button></div>
        </section>

        <section className="settings-panel system-panel compact-system-panel"><div className="settings-panel-head"><div><div className="settings-icon green"><ShieldCheck size={19} /></div><div><h3>System Status</h3><p>Live status of your CareerAI services.</p></div></div><button className="settings-outline-btn" onClick={checkSystem} disabled={checkingSystem}>{checkingSystem ? 'Checking…' : 'Refresh'} <RefreshCw size={14} /></button></div><div className="system-status-list"><SystemStatusRow label="Backend API" ok={systemReady?.ready !== false} /><SystemStatusRow label="Recommendation engine" ok={systemReady?.ready !== false} /><SystemStatusRow label="Application tracking" ok={systemReady?.ready !== false} /><SystemStatusRow label="Notification service" ok={systemReady?.ready !== false} /><SystemStatusRow label="Job source integrations" ok={true} /></div><div className="last-sync"><span>Last checked</span><b>{checkingSystem ? 'Checking…' : 'Just now'}</b></div></section>
      </div>
    </div>

    <div className="settings-middle-grid">
      <section className="settings-panel preferences-panel"><div className="settings-panel-head"><div><div className="settings-icon blue"><SlidersHorizontal size={19} /></div><div><h3>Career Preferences</h3><p>Tell CareerAI what you are looking for.</p></div></div><button className="settings-save-btn" onClick={savePreferences} disabled={saving}>{saving ? 'Saving…' : saved ? 'Saved ✓' : 'Save Changes'}</button></div>
        <PreferenceChips label="Preferred roles" values={preferences.roles} placeholder="Add role" onAdd={v => addChip('roles', v)} onRemove={v => removeChip('roles', v)} />
        <PreferenceChips label="Preferred locations" values={preferences.locations} placeholder="Add location" onAdd={v => addChip('locations', v)} onRemove={v => removeChip('locations', v)} />
        <div className="settings-field-row"><label><span>Experience level</span><select value={preferences.experience} onChange={e => update('experience', e.target.value)}><option>0–2 years</option><option>2–5 years</option><option>5+ years</option></select></label><div className="work-preference"><span>Work preference</span><div><button className={preferences.remote ? 'selected' : ''} onClick={() => update('remote', true)} type="button">Remote</button><button className={!preferences.remote ? 'selected' : ''} onClick={() => update('remote', false)} type="button">Hybrid / On-site</button></div></div></div>
        <ToggleRow label="Willing to relocate" value={preferences.relocate} onChange={v => update('relocate', v)} />
      </section>

      <section className="settings-panel"><div className="settings-panel-head"><div><div className="settings-icon gold"><Sparkles size={19} /></div><div><h3>Recommendation Preferences</h3><p>Customize how CareerAI prioritizes opportunities.</p></div></div></div><div className="toggle-list"><ToggleRow label="Prioritize skill match" value={preferences.skillMatch} onChange={v => update('skillMatch', v)} /><ToggleRow label="Consider preferred locations" value={preferences.preferredLocation} onChange={v => update('preferredLocation', v)} /><ToggleRow label="Consider experience level" value={preferences.experienceLevel} onChange={v => update('experienceLevel', v)} /><ToggleRow label="Include internship opportunities" value={preferences.internships} onChange={v => update('internships', v)} /><ToggleRow label="Show startup opportunities" value={preferences.startups} onChange={v => update('startups', v)} /></div></section>
    </div>

    <div className="settings-bottom-grid">
      <section className="settings-panel"><div className="settings-panel-head"><div><div className="settings-icon purple"><Bell size={19} /></div><div><h3>Notification Preferences</h3><p>Choose which career updates you want to receive.</p></div></div></div><div className="toggle-list"><ToggleRow label="New matching jobs" value={preferences.matchingJobs} onChange={v => update('matchingJobs', v)} /><ToggleRow label="Application status updates" value={preferences.applicationUpdates} onChange={v => update('applicationUpdates', v)} /><ToggleRow label="Interview reminders" value={preferences.interviewReminders} onChange={v => update('interviewReminders', v)} /><ToggleRow label="Weekly career summary" value={preferences.weeklySummary} onChange={v => update('weeklySummary', v)} /><ToggleRow label="Product updates & tips" value={preferences.productUpdates} onChange={v => update('productUpdates', v)} /></div></section>
    </div>
  </section>
}

function PreferenceChips({ label, values, placeholder, onAdd, onRemove }) {
  const [value, setValue] = useState('')
  const add = () => { onAdd(value); setValue('') }
  return <div className="preference-chips"><span className="preference-label">{label}</span><div className="chip-input-wrap">{values.map(item => <span className="preference-chip" key={item}>{item}<button type="button" onClick={() => onRemove(item)}><X size={12} /></button></span>)}<input value={value} placeholder={values.length ? 'Add another…' : placeholder} onChange={e => setValue(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }} /><button type="button" className="chip-add" onClick={add}>+ Add</button></div></div>
}

function ToggleRow({ label, value, onChange }) {
  return <div className="toggle-row"><span>{label}</span><button type="button" className={`toggle ${value ? 'on' : ''}`} onClick={() => onChange(!value)} aria-label={`${label}: ${value ? 'on' : 'off'}`}><span /></button></div>
}

function SystemStatusRow({ label, ok }) { return <div className={`system-status-row ${ok ? 'ok' : 'warn'}`}><span className="status-dot">{ok ? <Check size={11} /> : <CircleAlert size={11} />}</span><b>{label}</b><span>{ok ? 'Operational' : 'Needs attention'}</span></div> }

function Field({ label, value, onChange, type = 'text', placeholder }) { return <label><span>{label}</span><input type={type} value={value} placeholder={placeholder} onChange={e => onChange(e.target.value)} /></label> }
function Detail({ label, value }) { return <div><span>{label}</span><b>{value}</b></div> }
function AnalysisGroup({ title, items = [] }) { return <div className="analysis-group"><span>{title}</span>{items.length ? <div>{items.map(item => <i key={item}>{item}</i>)}</div> : <small>No extracted items</small>}</div> }
function EmptyState({ title, text }) { return <div className="empty-state"><Sparkles size={22} /><h3>{title}</h3><p>{text}</p></div> }
function slug(value = '') { return value.toLowerCase().replace(/[^a-z0-9]+/g, '-') }
function formatStatus(value = '') { return value.split('_').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(' ') }
function formatDate(value) { if (!value) return 'Recently'; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) }
