import { Button, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <Stack spacing={2} alignItems="center" justifyContent="center" sx={{ minHeight: '60vh' }}>
      <Typography variant="h3">404</Typography>
      <Typography color="text.secondary">Страница не найдена</Typography>
      <Button variant="contained" onClick={() => navigate('/')}>
        На главную
      </Button>
    </Stack>
  )
}
