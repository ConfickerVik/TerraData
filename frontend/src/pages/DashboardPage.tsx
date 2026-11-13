import { useNavigate } from 'react-router-dom'
import { Card, CardActionArea, CardContent, Grid, Stack, Typography } from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import DescriptionIcon from '@mui/icons-material/Description'
import MapIcon from '@mui/icons-material/Map'
import GavelIcon from '@mui/icons-material/Gavel'
import LocationCityIcon from '@mui/icons-material/LocationCity'
import AssessmentIcon from '@mui/icons-material/Assessment'
import { useAuth } from '../features/auth/useAuth'

const MODULES = [
  {
    title: 'Росреестр',
    description: 'Сведения об объекте по кадастровому номеру',
    path: '/rosreestr',
    icon: <SearchIcon />,
  },
  {
    title: 'Конвертер XML→PDF',
    description: 'Загрузка XML-выписки и конвертация в PDF',
    path: '/converter',
    icon: <DescriptionIcon />,
  },
  {
    title: 'НСПД',
    description: 'Кадастровая стоимость и геометрия объекта',
    path: '/nspd',
    icon: <MapIcon />,
  },
  {
    title: 'ФИАС',
    description: 'Адресный реестр, ObjectID и сведения об объектах',
    path: '/fias',
    icon: <LocationCityIcon />,
  },
  {
    title: 'СУДРФ',
    description: 'Определение судебного участка',
    path: '/sudrf',
    icon: <GavelIcon />,
  },
  {
    title: 'Аналитика',
    description: 'Сводный PDF-отчёт по объекту',
    path: '/analytics',
    icon: <AssessmentIcon />,
  },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Добро пожаловать{user ? `, ${user.username}` : ''}</Typography>
      <Typography color="text.secondary">
        TerraData — анализ объектов недвижимости по данным Росреестра, НСПД, ФИАС и СУДРФ.
      </Typography>
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
