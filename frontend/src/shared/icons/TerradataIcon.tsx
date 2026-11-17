import { useId } from 'react'
import type { ReactNode } from 'react'

// Иконки TerraData: 24x24, обводка 2px, зелёный градиент (как в icon pack).
const ICON_PATHS: Record<string, ReactNode> = {
  home: <path d="M3 11 12 3l9 8M5 9v12h14V9M9 21v-7h6v7" />,
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m15.5 15.5 5 5" />
    </>
  ),
  document: <path d="M6 3h8l4 4v14H6zM14 3v5h4M9 12h6M9 16h6" />,
  'folded-map': <path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15" />,
  'map-pin': (
    <>
      <path d="M12 21s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12Z" />
      <circle cx="12" cy="9" r="2" />
    </>
  ),
  scales: <path d="M12 4v16M7 20h10M5 7h14M5 7l-3 6h6zM19 7l-3 6h6z" />,
  chart: <path d="M4 20V12h4v8M10 20V7h4v13M16 20V4h4v16" />,
  'shield-check': <path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6zM8.5 12l2.3 2.3 4.8-5" />,
  settings: (
    <>
      <circle cx="12" cy="14" r="3" />
      <path d="M19 15l2 1-2 4-2-1-2 1v2H9v-2l-2-1-2 1-2-4 2-1v-2l-2-1 2-4 2 1 2-1V6h6v2l2 1 2-1 2 4-2 1z" />
    </>
  ),
}

interface TerradataIconProps {
  name: keyof typeof ICON_PATHS
  size?: number
}

export function TerradataIcon({ name, size = 24 }: TerradataIconProps) {
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '')
  const gradientId = `td-grad-${uid}`

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden="true"
      style={{ display: 'block' }}
    >
      <defs>
        <linearGradient
          id={gradientId}
          x1="3"
          y1="3"
          x2="21"
          y2="21"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#34C759" />
          <stop offset=".55" stopColor="#1B7F46" />
          <stop offset="1" stopColor="#052E16" />
        </linearGradient>
      </defs>
      <g
        fill="none"
        stroke={`url(#${gradientId})`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {ICON_PATHS[name]}
      </g>
    </svg>
  )
}
