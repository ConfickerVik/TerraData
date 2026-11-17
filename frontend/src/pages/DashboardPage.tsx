import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  CardActionArea,
  CardContent,
  Grid,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { ApiError } from '../api/client'
import type { ApiKeyOut } from '../api/types'
import { TerradataIcon } from '../shared/icons/TerradataIcon'
import { useAuth } from '../features/auth/useAuth'
import { listApiKeys } from '../features/auth/authApi'

const MODULES = [
  {
    title: 'Росреестр',
    description: 'Сведения об объекте по кадастровому номеру',
    path: '/rosreestr',
    icon: <TerradataIcon name="search" />,
  },
  {
    title: 'Конвертер XML→PDF',
    description: 'Загрузка XML-выписки и конвертация в PDF',
    path: '/converter',
    icon: <TerradataIcon name="document" />,
  },
  {
    title: 'НСПД',
    description: 'Кадастровая стоимость и геометрия объекта',
    path: '/nspd',
    icon: <TerradataIcon name="folded-map" />,
  },
  {
    title: 'ФИАС',
    description: 'Адресный реестр, ObjectID и сведения об объектах',
    path: '/fias',
    icon: <TerradataIcon name="map-pin" />,
  },
  {
    title: 'СУДРФ',
    description: 'Определение судебного участка',
    path: '/sudrf',
    icon: <TerradataIcon name="scales" />,
  },
  {
    title: 'Аналитика',
    description: 'Сводный PDF-отчёт по объекту',
    path: '/analytics',
    icon: <TerradataIcon name="chart" />,
  },
]

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h6">{value}</Typography>
      </CardContent>
    </Card>
  )
}

export function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [cadNum, setCadNum] = useState('')

  const keysQuery = useQuery<ApiKeyOut[], ApiError>({
    queryKey: ['api-keys'],
    queryFn: listApiKeys,
  })

  const activeKeys = (keysQuery.data ?? []).filter((key) => key.is_active).length

  const handleQuickSearch = () => {
    const trimmed = cadNum.trim()
    if (!trimmed) return
    navigate(`/rosreestr?cad_num=${encodeURIComponent(trimmed)}`)
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Добро пожаловать{user ? `, ${user.username}` : ''}</Typography>
      <Typography color="text.secondary">
        TerraData — анализ объектов недвижимости по данным Росреестра, НСПД, ФИАС и СУДРФ.
      </Typography>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ maxWidth: 640 }}>
        <TextField
          label="Быстрый поиск по кадастровому номеру"
          placeholder="38:36:000029:1028"
          value={cadNum}
          onChange={(event) => setCadNum(event.target.value)}
          fullWidth
        />
        <Button
          variant="contained"
          onClick={handleQuickSearch}
          disabled={!cadNum.trim()}
          sx={{ minWidth: 120 }}
        >
          Найти
        </Button>
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <StatCard
            label="Роль"
            value={user?.role === 'admin' ? 'Администратор' : 'Пользователь'}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <StatCard
            label="Суточный лимит"
            value={user?.request_limit != null ? String(user.request_limit) : 'По умолчанию'}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <StatCard label="Активных ключей" value={String(activeKeys)} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        {MODULES.map((module) => (
          <Grid item xs={12} sm={6} md={4} key={module.path}>
            <Card variant="outlined">
              <CardActionArea onClick={() => navigate(module.path)} sx={{ p: 1 }}>
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                    {module.icon}
                    <Typography variant="h6">{module.title}</Typography>
                  </Stack>
                  <Typography variant="body2" color="text.secondary">
                    {module.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  )
}
