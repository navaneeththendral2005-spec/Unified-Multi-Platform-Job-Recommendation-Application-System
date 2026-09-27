import { BriefcaseBusiness } from 'lucide-react'

export default function Logo({ compact = false }) {
  return (
    <div className="brand">
      <span className="brand-mark"><BriefcaseBusiness size={21} strokeWidth={2.6} /></span>
      {!compact && <span><strong>Career</strong>AI<small>Your intelligent career layer</small></span>}
    </div>
  )
}
