import { useState } from 'react'

/**
 * Local implementation inspired by Componentry's Layered Stack interaction.
 * Cards spring forward on hover while the surrounding cards subtly recede.
 */
export default function LayeredStack({ children, className = '' }) {
  const [active, setActive] = useState(null)
  const items = Array.isArray(children) ? children : [children]

  return (
    <div className={`layered-stack ${className}`} onMouseLeave={() => setActive(null)}>
      {items.map((child, index) => (
        <div
          key={child?.key ?? index}
          className={`layered-stack-item ${active === index ? 'is-active' : ''} ${active !== null && active !== index ? 'is-neighbor' : ''}`}
          onMouseEnter={() => setActive(index)}
        >
          {child}
        </div>
      ))}
    </div>
  )
}
