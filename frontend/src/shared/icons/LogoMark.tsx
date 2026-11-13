import { useId } from 'react'
import type { CSSProperties } from 'react'

interface LogoMarkProps {
  style?: CSSProperties
}

// Знак TerraData (абстрактная буква «T» из листа и стеблей).
// SVG-части (лист, сгиб, два стебля) — отдельные <path>, поэтому их можно
// при необходимости анимировать по одной через motion.path.
export function LogoMark({ style }: LogoMarkProps) {
  // useId + очистка: уникальные id градиентов/фильтра, чтобы несколько
  // экземпляров логотипа на одной странице не конфликтовали.
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '')
  const leafTop = `leafTop-${uid}`
  const leafFold = `leafFold-${uid}`
  const stemLeft = `stemLeft-${uid}`
  const stemRight = `stemRight-${uid}`
  const softShadow = `softShadow-${uid}`

  return (
    <svg
      viewBox="30 40 600 560"
      role="img"
      aria-label="TerraData"
      style={{ display: 'block', width: '100%', height: 'auto', ...style }}
    >
      <defs>
        <linearGradient id={leafTop} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#006B3B" />
          <stop offset="0.48" stopColor="#12C84B" />
          <stop offset="1" stopColor="#69E83C" />
        </linearGradient>
        <linearGradient id={leafFold} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#052E16" />
          <stop offset="1" stopColor="#1B7F46" />
        </linearGradient>
        <linearGradient id={stemLeft} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#087B43" />
          <stop offset="1" stopColor="#004D30" />
        </linearGradient>
        <linearGradient id={stemRight} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#48E33F" />
          <stop offset="1" stopColor="#0AA84A" />
        </linearGradient>
        <filter id={softShadow} x="-30%" y="-30%" width="160%" height="170%">
          <feGaussianBlur in="SourceAlpha" stdDeviation="10" />
          <feOffset dx="0" dy="12" result="offsetblur" />
          <feColorMatrix
            in="offsetblur"
            type="matrix"
            values="0 0 0 0 0.02 0 0 0 0 0.18 0 0 0 0 0.09 0 0 0 0.16 0"
          />
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <path
        d="M 52.028 189.548 C 74.028 114.548 132.028 61.548 219.028 61.548 L 599.028 61.548 C 599.028 61.548 597.028 110.548 562.028 146.548 C 523.028 187.548 474.028 190.548 419.028 190.548 L 52.028 190.548 L 52.028 189.548 Z"
        fill={`url(#${leafTop})`}
        filter={`url(#${softShadow})`}
      />
      <path
        d="M 52.028 189.548 L 219.028 189.548 C 302.028 189.548 384.028 131.548 454.028 61.548 L 599.028 61.548 C 599.028 61.548 597.028 110.548 562.028 146.548 C 523.028 187.548 474.028 190.548 419.028 190.548 L 52.028 189.548 Z"
        fill={`url(#${leafFold})`}
        opacity="0.52"
        filter={`url(#${softShadow})`}
      />
      <path
        d="M 285.499 210.348 L 344.028 210.348 L 344.028 409.548 C 344.028 444.548 315.518 477.602 285.518 495.602 L 196.028 545.548 L 196.028 304.548 C 196.028 250.548 216.258 221.998 285.499 210.348 Z"
        fill={`url(#${stemLeft})`}
        filter={`url(#${softShadow})`}
      />
      <path
        d="M 285.489 210.254 L 402.859 210.254 L 402.859 369.192 C 402.859 407.035 383.653 436.227 351.643 455.69 L 285.489 495.695 L 285.489 210.254 Z"
        fill={`url(#${stemRight})`}
        filter={`url(#${softShadow})`}
      />
    </svg>
  )
}
