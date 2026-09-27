import React, { useCallback, useEffect, useRef, useState } from 'react'

/**
 * CareerAI click feedback inspired by the supplied ClickSpark usage.
 * Props mirror the provided example: sparkColor, sparkSize, sparkRadius,
 * sparkCount and duration. It adds a lightweight burst at the click point
 * without replacing or changing the wrapped content.
 */
export default function ClickSpark({
  children,
  sparkColor = '#000000',
  sparkSize = 11,
  sparkRadius = 15,
  sparkCount = 8,
  duration = 400,
  className = '',
}) {
  const rootRef = useRef(null)
  const [bursts, setBursts] = useState([])
  const idRef = useRef(0)

  const handlePointerDown = useCallback((event) => {
    if (event.button !== 0) return
    const root = rootRef.current
    if (!root) return

    const rect = root.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    const id = ++idRef.current
    const sparks = Array.from({ length: Math.max(1, sparkCount) }, (_, index) => ({
      id: `${id}-${index}`,
      angle: (360 / Math.max(1, sparkCount)) * index + (Math.random() * 12 - 6),
      distance: sparkRadius * (0.8 + Math.random() * 0.35),
      size: sparkSize * (0.7 + Math.random() * 0.45),
    }))

    setBursts((current) => [...current.slice(-3), { id, x, y, sparks }])
    window.setTimeout(() => {
      setBursts((current) => current.filter((burst) => burst.id !== id))
    }, duration + 40)
  }, [duration, sparkCount, sparkRadius, sparkSize])

  useEffect(() => {
    return () => setBursts([])
  }, [])

  return (
    <div
      ref={rootRef}
      className={`click-spark-root ${className}`}
      onPointerDown={handlePointerDown}
    >
      {children}
      <span className="click-spark-layer" aria-hidden="true">
        {bursts.map((burst) => (
          <span
            className="click-spark-burst"
            key={burst.id}
            style={{ left: burst.x, top: burst.y }}
          >
            {burst.sparks.map((spark) => (
              <span
                className="click-spark-particle"
                key={spark.id}
                style={{
                  '--spark-angle': `${spark.angle}deg`,
                  '--spark-distance': `${spark.distance}px`,
                  '--spark-size': `${spark.size}px`,
                  '--spark-color': sparkColor,
                  '--spark-duration': `${duration}ms`,
                }}
              />
            ))}
          </span>
        ))}
      </span>
    </div>
  )
}
