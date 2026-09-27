import * as React from 'react'
import { motion, useReducedMotion } from 'motion/react'

/**
 * CareerAI adaptation of the supplied Originkit Label Slide Button.
 * The visible label is intentionally kept unchanged; only the interaction,
 * icon treatment, and visual styling are replaced.
 */
export default function LabelSlideButton({
  children,
  onClick,
  href,
  variant = 'primary',
  className = '',
  showIcon = true,
  type = 'button',
}) {
  const reduceMotion = useReducedMotion()
  const [hovered, setHovered] = React.useState(false)
  const label = React.useMemo(() => String(children ?? ''), [children])
  const Component = href ? motion.a : motion.button

  const variants = {
    primary: {
      rest: { backgroundColor: '#ffc400', color: '#11130f', borderColor: 'rgba(180,128,0,.22)' },
      hover: { backgroundColor: '#11130f', color: '#fffdf8', borderColor: '#11130f' },
      iconRest: '#11130f',
      iconHover: '#ffc400',
    },
    ghost: {
      rest: { backgroundColor: 'rgba(255,255,255,.62)', color: '#11130f', borderColor: '#d9c78d' },
      hover: { backgroundColor: '#ffc400', color: '#11130f', borderColor: '#ffc400' },
      iconRest: '#11130f',
      iconHover: '#11130f',
    },
  }

  const theme = variants[variant]
  const transition = reduceMotion
    ? { duration: 0 }
    : { type: 'tween', duration: 0.35, ease: [0.16, 1, 0.3, 1] }

  const iconTransition = reduceMotion
    ? { duration: 0 }
    : { duration: 0.25, ease: 'easeInOut' }

  const content = (
    <>
      <span className="label-slide-text">
        <span className="label-slide-measure">{label}</span>
        <motion.span
          className="label-slide-layer"
          animate={{ y: hovered ? '-100%' : '0%' }}
          transition={transition}
        >
          {label}
        </motion.span>
        <motion.span
          className="label-slide-layer label-slide-enter"
          animate={{ y: hovered ? '0%' : '100%' }}
          transition={transition}
        >
          {label}
        </motion.span>
      </span>

      {showIcon && (
        <span className="label-slide-icon-wrap" aria-hidden="true">
          <motion.span
            className="label-slide-icon"
            animate={{ x: hovered ? 18 : 0, y: hovered ? -18 : 0, opacity: hovered ? 0 : 1 }}
            transition={iconTransition}
            style={{ backgroundColor: hovered ? theme.iconHover : theme.iconRest, color: hovered ? '#11130f' : '#fffdf8' }}
          >
            →
          </motion.span>
          <motion.span
            className="label-slide-icon label-slide-icon-in"
            animate={{ x: hovered ? 0 : -18, y: hovered ? 0 : 18, opacity: hovered ? 1 : 0 }}
            transition={iconTransition}
            style={{ backgroundColor: hovered ? theme.iconHover : theme.iconRest, color: hovered ? '#11130f' : '#fffdf8' }}
          >
            →
          </motion.span>
        </span>
      )}
    </>
  )

  return (
    <Component
      href={href}
      type={href ? undefined : type}
      className={`label-slide-button label-slide-${variant} ${className}`}
      initial={false}
      animate={hovered ? theme.hover : theme.rest}
      whileTap={reduceMotion ? undefined : { scale: 0.97 }}
      transition={transition}
      onPointerEnter={() => setHovered(true)}
      onPointerLeave={() => setHovered(false)}
      onFocus={() => setHovered(true)}
      onBlur={() => setHovered(false)}
      onClick={onClick}
    >
      {content}
    </Component>
  )
}
