import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Stack, TextField, Typography } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import { useAuth } from '../features/auth/useAuth'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const mutation = useMutation<void, ApiError, void>({
    mutationFn: () => login(username, password),
    onSuccess: () => navigate('/'),
  })

  return (
    <Stack spacing={2}>
      <Typography variant="h5" align="center">
        Вход
      </Typography>
      <TextField
        label="Имя пользователя"
        value={username}
        onChange={(event) => setUsername(event.target.value)}
        fullWidth
        autoFocus
      />
      <TextField
        label="Пароль"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        fullWidth
      />
      {mutation.isError && <Alert severity="error">{getApiErrorDetail(mutation.error)}</Alert>}
      <Button
        variant="contained"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || !username || !password}
        fullWidth
      >
        {mutation.isPending ? 'Вход…' : 'Войти'}
      </Button>
      <Button variant="text" onClick={() => navigate('/register')}>
        Нет аккаунта? Зарегистрироваться
      </Button>
    </Stack>
  )
}
