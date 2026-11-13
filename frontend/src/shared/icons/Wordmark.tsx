interface WordmarkProps {
  fontSize?: string
}

// Текстовая часть логотипа «TerraData» — отдельный HTML-элемент (не SVG),
// чтобы её можно было анимировать и масштабировать независимо от знака.
// Двухцветная заливка повторяет градиенты исходного SVG (wordTerra / wordData).
export function Wordmark({ fontSize = 'clamp(28px, 5vw, 60px)' }: WordmarkProps) {
  return (
    <span
      style={{
        fontSize,
        fontWeight: 800,
        letterSpacing: '-0.02em',
        lineHeight: 1,
        whiteSpace: 'nowrap',
        display: 'inline-block',
        fontFamily: '"TikTok Sans", Inter, "Segoe UI", Roboto, sans-serif',
      }}
    >
      <span
        style={{
          background: 'linear-gradient(180deg, #052E16 0%, #073D25 100%)',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          color: 'transparent',
        }}
      >
        Terra
      </span>
      <span
        style={{
          background: 'linear-gradient(180deg, #18D64A 0%, #0AB743 100%)',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          color: 'transparent',
        }}
      >
        Data
      </span>
    </span>
  )
}
