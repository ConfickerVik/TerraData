import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  LinearProgress,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import RestartAltIcon from '@mui/icons-material/RestartAlt'
import { useMutation } from '@tanstack/react-query'
import { ApiError, getApiErrorDetail } from '../api/client'
import { generateReport } from '../features/analytics/analyticsApi'
import type { GenerateReportResult } from '../features/analytics/analyticsApi'

export function AnalyticsPage() {
  const [cadNum, setCadNum] = useState('')
  const [includeNspd, setIncludeNspd] = useState(true)
  const [includeFias, setIncludeFias] = useState(true)
  const [includeSudrf, setIncludeSudrf] = useState(true)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [downloadName, setDownloadName] = useState('report.pdf')

  const mutation = useMutation<GenerateReportResult, ApiError, void>({
    mutationFn: () =>
      generateReport({
        cad_num: cadNum.trim(),
        include_nspd: includeNspd,
        include_fias: includeFias,
        include_sudrf: includeSudrf,
      }),
    onSuccess: (result) => {
      setPdfUrl(URL.createObjectURL(result.blob))
      setDownloadName(result.filename)
    },
  })

  // Освобождаем object URL при смене файла и размонтировании страницы.
  useEffect(() => {
    if (!pdfUrl) return
    return () => URL.revokeObjectURL(pdfUrl)
  }, [pdfUrl])

  const handleDownload = () => {
    if (!pdfUrl) return
    const anchor = document.createElement('a')
    anchor.href = pdfUrl
    anchor.download = downloadName
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  }

  const handleReset = () => {
    mutation.reset()
    setPdfUrl(null)
    setDownloadName('report.pdf')
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Аналитика</Typography>
      <Typography variant="body2" color="text.secondary">
        Сводный PDF-отчёт об объекте недвижимости: Росреестр + НСПД + ФИАС + СУДРФ.
      </Typography>

      {!pdfUrl && (
        <Stack spacing={2} sx={{ maxWidth: 560 }}>
          <TextField
            label="Кадастровый номер"
            placeholder="38:36:000029:1028"
            value={cadNum}
            onChange={(event) => setCadNum(event.target.value)}
            fullWidth
          />

          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Источники данных
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={includeNspd}
                onChange={(_event, checked) => setIncludeNspd(checked)}
              />
            }
            label="НСПД"
          />
          <FormControlLabel
            control={
              <Switch
                checked={includeFias}
                onChange={(_event, checked) => setIncludeFias(checked)}
              />
            }
            label="ФИАС"
          />
          <FormControlLabel
            control={
              <Switch
                checked={includeSudrf}
                onChange={(_event, checked) => setIncludeSudrf(checked)}
              />
            }
            label="СУДРФ"
          />
          <Typography variant="caption" color="text.secondary">
            Росреестр — ядро отчёта, включается всегда.
          </Typography>

          <Box>
            <Button
              variant="contained"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending || !cadNum.trim()}
              startIcon={
                mutation.isPending ? <CircularProgress size={20} color="inherit" /> : undefined
              }
            >
              {mutation.isPending ? 'Формируем отчёт…' : 'Сформировать отчёт'}
            </Button>
          </Box>

          {mutation.isPending && (
            <Stack spacing={1}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary">
                Собираем данные: Росреестр → НСПД → ФИАС → СУДРФ. Это может занять до минуты…
              </Typography>
            </Stack>
          )}

          {mutation.isError && (
            <Alert severity="error">{getApiErrorDetail(mutation.error)}</Alert>
          )}
        </Stack>
      )}

      {pdfUrl && (
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
            <Button variant="contained" startIcon={<DownloadIcon />} onClick={handleDownload}>
              Скачать PDF
            </Button>
            <Button variant="outlined" startIcon={<RestartAltIcon />} onClick={handleReset}>
              Сформировать заново
            </Button>
          </Stack>

          <Typography variant="body2" color="text.secondary">
            {downloadName}
          </Typography>

          <Box
            sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}
          >
            <iframe
              src={pdfUrl}
              title="Предпросмотр PDF"
              style={{ width: '100%', height: '70vh', minHeight: 400, border: 'none', display: 'block' }}
            />
          </Box>
        </Stack>
      )}
    </Stack>
  )
}
