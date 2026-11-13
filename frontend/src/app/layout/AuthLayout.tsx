import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Box } from '@mui/material'
import { Outlet } from 'react-router-dom'
import { LogoMark } from '../../shared/icons/LogoMark'
import { Wordmark } from '../../shared/icons/Wordmark'

// Длительность «центрированной» фазы интро до смещения лого влево.
const INTRO_DURATION_MS = 2000

// Размеры логотипа адаптивны: на большом экране знак и текст растут,
// чтобы не было «маленькой иконки в пустом экране».
const ICON_SIZE = 'clamp(96px, 18vw, 220px)'
const FONT_SIZE = 'clamp(28px, 5vw, 60px)'

interface BrandProps {
  intro?: boolean
}

function Brand({ intro = false }: BrandProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 'clamp(8px, 1.5vw, 20px)' }}>
      {/* Знак появляется первым (при intro) */}
      <motion.div
        initial={intro ? { opacity: 0, scale: 0.6 } : false}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        style={{ width: ICON_SIZE, flexShrink: 0, position: 'relative', zIndex: 2 }}
      >
        <LogoMark />
      </motion.div>

      {/* Текст выезжает из-за знака (при intro) */}
      <motion.div
        initial={intro ? { opacity: 0, x: '-0.5em' } : false}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: intro ? 0.5 : 0, ease: 'easeOut' }}
        style={{ fontSize: FONT_SIZE, lineHeight: 1, position: 'relative', zIndex: 1 }}
      >
        <Wordmark fontSize={FONT_SIZE} />
      </motion.div>
    </Box>
  )
}

export function AuthLayout() {
  const [intro, setIntro] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setIntro(false), INTRO_DURATION_MS)
    return () => clearTimeout(timer)
  }, [])

  return (
    <Box sx={{ position: 'relative', minHeight: '100vh', overflow: 'hidden', bgcolor: '#ffffff' }}>
      {/* Итоговая раскладка: лого слева, форма справа */}
      <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', minHeight: '100vh' }}>
        <Box
          sx={{
            flex: 1,
            display: { xs: 'none', md: 'flex' },
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%)',
            px: 4,
          }}
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: intro ? 0 : 1 }}
            transition={{ duration: 0.4, delay: 0.55 }}
          >
            <Brand />
          </motion.div>
        </Box>

        <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
          {!intro && (
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.45, ease: 'easeOut' }}
              style={{ width: '100%', maxWidth: 400 }}
            >
              <Outlet />
            </motion.div>
          )}
        </Box>
      </Box>

      {/* Сплэш-заставка с интро-анимацией (поверх итоговой раскладки) */}
      <motion.div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
          background: '#ffffff',
        }}
        animate={{ opacity: intro ? 1 : 0 }}
        transition={{ duration: 0.4, delay: intro ? 0 : 0.6 }}
      >
        <motion.div
          initial={false}
          animate={{ x: intro ? '0vw' : '-25vw' }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <Brand intro />
        </motion.div>
      </motion.div>
    </Box>
  )
}
