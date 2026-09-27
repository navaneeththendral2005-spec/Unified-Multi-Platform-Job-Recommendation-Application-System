import { ArrowUpRight, Bell, BriefcaseBusiness, ChevronRight, Search, Sparkles } from 'lucide-react'

const jobs = [
  { title: 'Backend Engineer', company: 'Zoho Corporation', location: 'Chennai · Hybrid', score: 92, skills: ['Python', 'FastAPI', 'PostgreSQL'], source: 'LinkedIn' },
  { title: 'Software Engineer', company: 'TCS', location: 'Bengaluru · Full-time', score: 87, skills: ['Python', 'API', 'System Design'], source: 'Naukri' },
  { title: 'Data Analyst', company: 'Accenture', location: 'Chennai · Remote', score: 84, skills: ['SQL', 'Python', 'Analytics'], source: 'Indeed' },
]

export default function MockDashboard() {
  return (
    <div className="dashboard-tilt-wrap">
      <div className="dashboard-tilt-shadow" />
      <div className="dashboard-window">
        <aside className="mini-sidebar">
          <div className="mini-logo"><BriefcaseBusiness size={16} /> CareerAI</div>
          {['Dashboard', 'Discover Jobs', 'Recommendations', 'Applications', 'Resume & Profile', 'Notifications', 'Settings'].map((item, i) => (
            <div key={item} className={`mini-nav ${i === 0 ? 'active' : ''}`}>{item}</div>
          ))}
          <div className="mini-user"><div className="avatar">P</div><span>Priya S<small>Student</small></span><ChevronRight size={13} /></div>
        </aside>
        <section className="mini-main">
          <header className="mini-top"><span>Career workspace</span><div><Bell size={17} /><span className="dot">3</span><div className="avatar">P</div></div></header>
          <div className="mini-heading"><div><p className="eyebrow">OVERVIEW</p><h3>Good evening, Priya <span>👋</span></h3><p>Your career opportunities, intelligently connected.</p></div></div>
          <div className="mini-search"><Search size={16} /><span>Search jobs, skills, companies...</span><button><Search size={15}/></button></div>
          <div className="mini-stats">
            <div><b>18</b><span>Skills detected</span></div><div><b>4</b><span>Projects found</span></div><div><b>6</b><span>Suggested roles</span></div><div><b>92%</b><span>Profile complete</span></div>
          </div>
          <div className="mini-section-head"><span>Recommended for you</span><a>View all <ArrowUpRight size={13}/></a></div>
          <div className="mini-jobs">
            {jobs.map((job) => <div className="mini-job" key={job.title}>
              <div className="company-logo">{job.company[0]}</div><div className="job-copy"><b>{job.title}</b><span>{job.company}</span><span>{job.location}</span><div className="skill-row">{job.skills.map(s => <i key={s}>{s}</i>)}</div></div>
              <div className="job-side"><strong>{job.score}%</strong><small>Match</small><span>{job.source}</span></div>
            </div>)}
          </div>
          <div className="mini-ai"><Sparkles size={15}/><span><b>AI insight:</b> Your strongest matches are backend roles using Python and API technologies.</span></div>
        </section>
      </div>
    </div>
  )
}
