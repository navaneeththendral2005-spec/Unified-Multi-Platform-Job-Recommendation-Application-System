import { useState } from 'react'
import { ArrowRight, BellRing, BrainCircuit, Check, CheckCircle2, CirclePlay, Clock3, MapPinned, Network, Radar, Send, Sparkles, Target, TrendingUp, UserRound } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import Logo from '../components/Logo'
import LabelSlideButton from '../components/LabelSlideButton'
import LayeredStack from '../components/LayeredStack'

const steps = [
  ['01', 'Build your profile', 'Upload your resume and define the roles and locations you care about.', BrainCircuit],
  ['02', 'Get AI insights', 'Turn your experience, projects and skills into structured candidate intelligence.', Sparkles],
  ['03', 'Discover opportunities', 'Explore relevant opportunities from supported and authorized sources.', Radar],
  ['04', 'Understand & decide', 'See match signals, skill gaps, source details and job context before applying.', Target],
  ['05', 'Apply legitimately', 'Use the appropriate application flow for the opportunity and platform.', Send],
  ['06', 'Track everything', 'Keep application progress, events and notifications together in one workspace.', TrendingUp],
]

export default function LandingPage({ onGetStarted }) {
  return <div className="landing" id="top">
    <div className="ambient ambient-a"/><div className="ambient ambient-b"/>
    <nav className="nav container">
      <Logo />
      <NavLinks />
      <div className="nav-actions"><LabelSlideButton variant="ghost" showIcon={false} onClick={onGetStarted}>Login</LabelSlideButton><LabelSlideButton variant="primary" onClick={onGetStarted}>Get Started</LabelSlideButton></div>
    </nav>

    <main>
      <section className="hero container">
        <div className="hero-copy">
          <div className="pill"><Sparkles size={15}/> AI-Powered <span/> Multi-Platform <span/> Opportunities That Fit You</div>
          <h1>Your career,<br/><em>intelligently</em> connected.</h1>
          <p>An intelligent career platform that understands your profile, connects you with relevant opportunities, and helps you make informed career decisions — all in one place.</p>
          <div className="hero-actions"><LabelSlideButton variant="primary" onClick={onGetStarted} className="btn-large">Get Started Free</LabelSlideButton><a href="#how" className="watch"><CirclePlay size={20}/> Watch how it works</a></div>
          <div className="hero-trust"><div><BrainCircuit size={21}/><b>AI Resume Analysis</b><small>Understand your skills and potential</small></div><div><Network size={21}/><b>Multi-Platform</b><small>Opportunities from connected sources</small></div><div><Target size={21}/><b>Personalized</b><small>Recommendations built around you</small></div><div><TrendingUp size={21}/><b>Track Applications</b><small>Stay updated at every step</small></div></div>
        </div>
        <div className="hero-visual" aria-label="CareerAI intelligent career assistant">
          <div className="hero-character-glow" />
          <div className="hero-character-orbit orbit-a" />
          <div className="hero-character-orbit orbit-b" />
          <div className="character-stage">
            <div className="character-shadow" />
            <img className="hero-character" src="/assets/careerai-character.png" alt="CareerAI animated assistant" />
          </div>
          <div className="float-card character-card float-one"><Sparkles size={15}/><span>AI Match</span><b>92%</b></div>
          <div className="float-card character-card float-two"><MapPinned size={15}/><span>Location fit</span><b>Excellent</b></div>
          <div className="float-card character-card float-three"><Target size={15}/><span>Opportunities</span><b>Personalized</b></div>

          <div className="orbit-object skill-object skill-python"><span>Py</span><b>Python</b></div>
          <div className="orbit-object skill-object skill-ai"><Sparkles size={14}/><b>AI</b></div>
          <div className="orbit-object skill-object skill-api"><Network size={14}/><b>API</b></div>
          <div className="orbit-object source-object"><span className="source-dot"/><b>Multi-source</b></div>
          <div className="floating-cube cube-one"><span/></div>
          <div className="floating-cube cube-two"><span/></div>
          <div className="spark spark-one">✦</div>
          <div className="spark spark-two">✧</div>
          <div className="spark spark-three">✦</div>
        </div>
      </section>

      <section className="vision-section" id="vision">
        <section className="vision-band"><div className="container vision-inner"><div><p className="eyebrow">THE CAREERAI IDEA</p><h2>Understand. Discover. Decide. Apply. Track.</h2></div><p>CareerAI is designed as an intelligent layer between a candidate and the job market — starting with who you are, not just what jobs exist.</p></div></section>

        <section className="features container" id="features"><div className="section-head vision-section-head"><p className="eyebrow">BUILT AROUND YOU</p><h2>One intelligent workspace.<br/><span>Every part of your career journey.</span></h2></div><div className="feature-grid"><Feature index={0} icon={BrainCircuit} title="Candidate Intelligence" text="Resume analysis, skills, projects, experience and career preferences become a structured profile." visual={<CandidateVisual/>}/><Feature index={1} icon={Target} title="Explainable Recommendations" text="See match signals, matched skills, missing skills and the reasons behind an opportunity." visual={<RecommendationVisual/>}/><Feature index={2} icon={Network} title="Multi-Platform Architecture" text="Discover opportunities through supported sources while preserving source attribution." visual={<PlatformVisual/>}/><Feature index={3} icon={TrendingUp} title="Application Intelligence" text="Follow application status, history, events and notifications from one place." visual={<ApplicationVisual/>}/></div></section>
      </section>

      <section className="how how-premium" id="how">
        <div className="container">
          <div className="section-head center how-premium-head">
            <p className="eyebrow">HOW IT WORKS</p>
            <h2>From your profile to real <span>opportunities.</span></h2>
            <p>A simple, intelligent flow built around the way people actually make career decisions.</p>
          </div>

          <LayeredStack className="how-card-stack">
            {steps.map(([n, title, text, Icon]) => (
              <HowItWorksCard key={n} number={n} title={title} text={text} Icon={Icon} />
            ))}
          </LayeredStack>
        </div>
      </section>

      <section className="about2-section" id="about">
        <div className="container">
          <div className="about2-hero">
            <div className="about2-visual" aria-label="CareerAI opportunity journey illustration">
              <div className="about2-visual-backdrop" />
              <div className="about2-art-frame">
                <img src="/assets/about-careerai-visual.png" alt="CareerAI opportunity journey" />
                <div className="about2-art-sheen" />
              </div>

              <div className="about2-float about2-float-resume"><span className="about2-mini-icon"><UserRound size={14}/></span><div><b>Resume understood</b><span>Profile intelligence ready</span></div><Check size={15}/></div>
              <div className="about2-float about2-float-search"><span className="about2-mini-icon"><Radar size={14}/></span><div><b>Opportunities found</b><span>Relevant matches nearby</span></div></div>
              <div className="about2-float about2-float-track"><span className="about2-mini-icon"><TrendingUp size={14}/></span><div><b>Journey connected</b><span>Discovery → tracking</span></div></div>
              <div className="about2-floating-chip about2-chip-one"><Sparkles size={14}/> AI intelligence</div>
              <div className="about2-floating-chip about2-chip-two"><Network size={14}/> Connected sources</div>
              <div className="about2-spark about2-spark-one">✦</div>
              <div className="about2-spark about2-spark-two">✧</div>
              <div className="about2-spark about2-spark-three">✦</div>
              <div className="about2-orb about2-orb-one" />
              <div className="about2-orb about2-orb-two" />
            </div>
            <div className="about2-copy">
              <p className="eyebrow">ABOUT CAREERAI</p>
              <h2>Built for<br/><span>your next chapter.</span></h2>
              <p>CareerAI is a unified intelligent career layer that understands your profile, connects you with relevant opportunities across supported sources, and helps you manage the journey from discovery to application tracking.</p>
              <div className="about2-signature"><span>More opportunities.</span><b>A clearer tomorrow.</b><i /></div>
              <div className="about2-pillars">
                <div><span><UserRound size={19}/></span><b>Personalized</b><small>to your goals</small></div>
                <div><span><Sparkles size={19}/></span><b>Smarter</b><small>job discovery</small></div>
                <div><span><TrendingUp size={19}/></span><b>Simpler</b><small>career tracking</small></div>
              </div>
            </div>
          </div>

          <div className="about2-mission">
            <div><p className="eyebrow">OUR MISSION</p><h3>Understand the person.<br/><span>Connect the opportunity.</span></h3></div>
            <p>We believe career discovery should begin with the candidate, not with an endless list of jobs. CareerAI turns your resume, skills, experience and preferences into useful intelligence, then carries that context into opportunity discovery and application tracking.</p>
          </div>

          <div className="about2-work">
            <div className="about2-work-head"><div><p className="eyebrow">WHAT WE DO</p><h2>One intelligent workspace.<br/><span>Every stage stays connected.</span></h2></div><p>From understanding your profile to keeping applications organized, CareerAI brings the pieces together without losing context.</p></div>
            <div className="about2-flow">
              <About2FlowCard number="01" icon={UserRound} title="Understand you" text="Build structured candidate intelligence from your profile."/>
              <div className="about2-flow-arrow"><ArrowRight size={16}/></div>
              <About2FlowCard number="02" icon={Network} title="Find opportunities" text="Discover relevant openings from supported sources." highlighted/>
              <div className="about2-flow-arrow"><ArrowRight size={16}/></div>
              <About2FlowCard number="03" icon={Target} title="Guide decisions" text="See match signals and context before applying."/>
              <div className="about2-flow-arrow"><ArrowRight size={16}/></div>
              <About2FlowCard number="04" icon={TrendingUp} title="Keep you on track" text="Follow applications, events and notifications." highlighted/>
            </div>
          </div>
        </div>
      </section>

      <section className="cta container" id="cta"><div className="cta-orb orb-one"/><div className="cta-orb orb-two"/><div className="cta-content"><div className="pill dark-pill"><Sparkles size={14}/> Your intelligent career layer</div><h2>Stop searching everywhere.<br/><em>Start connecting everything.</em></h2><p>Build your profile once. Understand your opportunities. Keep your applications together.</p><button className="btn btn-dark btn-large" onClick={onGetStarted}>Enter CareerAI <ArrowRight size={18}/></button></div></section>
    </main>
    <footer className="footer container"><Logo compact/><span>© 2026 CareerAI. Built for informed career decisions.</span><div><a>Privacy</a><a>Terms</a><a>GitHub</a></div></footer>
  </div>
}


function NavLinks() {
  const reduceMotion = useReducedMotion()
  const [hovered, setHovered] = useState(null)
  const links = [
    ['Home', '#top'],
    ['How It Works', '#how'],
    ['Our Vision', '#vision'],
    ['About', '#about'],
  ]
  const active = hovered ?? 'Home'

  return (
    <div className="nav-links" onMouseLeave={() => setHovered(null)}>
      {links.map(([label, href]) => (
        <a
          key={label}
          href={href}
          className={active === label ? 'is-selected' : ''}
          onMouseEnter={() => setHovered(label)}
          onFocus={() => setHovered(label)}
          onBlur={() => setHovered(null)}
        >
          <span>{label}</span>
          {active === label && (
            <motion.span
              layoutId="nav-hover-slider"
              className="nav-hover-slider"
              transition={reduceMotion ? { duration: 0 } : { type: 'spring', stiffness: 520, damping: 34, mass: 0.55 }}
            />
          )}
        </a>
      ))}
    </div>
  )
}

function HowItWorksCard({ number, title, text, Icon }) {
  return <article className="how-card">
    <div className={`how-card-visual how-visual-${number}`}>
      <HowItWorksVisual number={number} />
      <span className="how-card-glow" />
    </div>
    <div className="how-card-body">
      <div className="how-card-meta"><span>{number}</span><Icon size={22}/></div>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  </article>
}

function HowItWorksVisual({ number }) {
  if (number === '01') return <div className="how-ui profile-ui">
    <div className="ui-window-head"><span /><span /><span /></div>
    <div className="profile-ui-title"><span className="ui-avatar"><UserRound size={15}/></span><b>Your Profile</b></div>
    <div className="profile-ui-row"><UserRound size={12}/> Skills</div>
    <div className="profile-ui-row"><BrainCircuit size={12}/> Experience</div>
    <div className="profile-ui-row"><Target size={12}/> Projects</div>
    <div className="profile-ui-row"><MapPinned size={12}/> Preferences</div>
  </div>

  if (number === '02') return <div className="how-ui ai-ui">
    <div className="ai-core"><Sparkles size={30}/><b>AI</b></div>
    <span className="ai-tag tag-skills">Skills</span><span className="ai-tag tag-exp">Experience</span><span className="ai-tag tag-projects">Projects</span><span className="ai-tag tag-pref">Preferences</span>
    <div className="ai-signal signal-one"/><div className="ai-signal signal-two"/><div className="ai-signal signal-three"/>
  </div>

  if (number === '03') return <div className="how-ui jobs-ui">
    <div className="jobs-search"><span>Search roles, companies or skills...</span><Radar size={14}/></div>
    <div className="jobs-layout"><div className="jobs-side"><b>All Opportunities</b><span>Recommended</span><span>Remote</span><span>Full-time</span></div><div className="jobs-list"><div><b>Software Engineer</b><small>Google · Bengaluru · Full-time</small></div><div><b>ML Engineer</b><small>Microsoft · Hyderabad · Full-time</small></div><div><b>Applied Scientist</b><small>Amazon · Remote · Full-time</small></div></div></div>
  </div>

  if (number === '04') return <div className="how-ui match-ui">
    <div className="match-title"><span>Match Analysis</span><b>92%</b></div>
    <div className="match-ring"><strong>92%</strong><small>Match</small></div>
    <div className="match-checks"><span><CheckCircle2 size={12}/> Skills match</span><span><CheckCircle2 size={12}/> Experience match</span><span><CheckCircle2 size={12}/> Project relevance</span><span><CheckCircle2 size={12}/> Growth potential</span></div>
  </div>

  if (number === '05') return <div className="how-ui apply-ui">
    <div className="apply-button"><Send size={28}/><b>Apply</b></div>
    <div className="apply-cursor"/>
    <div className="apply-glint"/>
  </div>

  return <div className="how-ui track-ui">
    <div className="track-head"><b>Application Tracking</b><BellRing size={13}/></div>
    <div className="track-line"/>
    <div className="track-step done"><span><CheckCircle2 size={12}/></span><b>Applied</b><small>Apr 12, 2026</small></div>
    <div className="track-step active"><span><Clock3 size={12}/></span><b>In Review</b><small>Apr 16, 2026</small></div>
    <div className="track-step active"><span><UserRound size={12}/></span><b>Interview</b><small>Apr 22, 2026</small></div>
    <div className="track-step muted"><span><span className="track-dot"/></span><b>Offer</b></div>
  </div>
}

function About2FlowCard({ number, icon: Icon, title, text, highlighted = false }) {
  return <article className={`about2-flow-card${highlighted ? ' highlighted' : ''}`}>
    <div className="about2-flow-top"><span>{number}</span><Icon size={19}/></div>
    <div className="about2-flow-icon"><Icon size={19}/></div>
    <h3>{title}</h3>
    <p>{text}</p>
  </article>
}

function Feature({ index, icon: Icon, title, text, visual }) {
  return <article className="feature" style={{ '--feature-index': index }}>
    <div className="feature-glow" aria-hidden="true"/>
    <div className="feature-topline">
      <div className="feature-icon"><Icon size={23}/></div>
      <div className="feature-visual" aria-hidden="true">{visual}</div>
    </div>
    <h3>{title}</h3>
    <p>{text}</p>
    <div className="feature-check" aria-hidden="true"><Check size={16}/></div>
  </article>
}

function CandidateVisual() {
  return <div className="mini-profile">
    <div className="mini-profile-head"><span className="mini-avatar"><UserRound size={12}/></span><span><b>Profile</b><i>Structured</i></span></div>
    <div className="mini-lines"><span/><span/><span className="short"/></div>
    <div className="mini-tags"><i>Skills</i><i>Experience</i><i>Preferences</i></div>
  </div>
}

function RecommendationVisual() {
  return <div className="mini-match">
    <div className="match-head"><span>AI Match</span><b>92%</b></div>
    <div className="match-bar"><span/></div>
    <div className="match-points"><span><CheckCircle2 size={10}/> Matched skills</span><span><CheckCircle2 size={10}/> Relevant experience</span><span><CheckCircle2 size={10}/> Growth potential</span></div>
  </div>
}

function PlatformVisual() {
  return <div className="mini-platforms">
    <span className="platform-node node-a">in</span><span className="platform-node node-b">W</span><span className="platform-node node-c">N</span><span className="platform-node node-d">•••</span>
    <i className="platform-line line-a"/><i className="platform-line line-b"/><i className="platform-line line-c"/>
  </div>
}

function ApplicationVisual() {
  return <div className="mini-application">
    <div className="application-window"><span/><span/><span/></div>
    <div className="application-status"><span><CheckCircle2 size={10}/> Application Sent</span><span><Clock3 size={10}/> In Review</span><span><BellRing size={10}/> Updates</span></div>
  </div>
}
