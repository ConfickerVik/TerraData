import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { Alert, Box, Button, CircularProgress, Stack, Typography } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import DownloadIcon from '@mui/icons-material/Download'
import RestartAltIcon from '@mui/icons-material/RestartAlt'
import { convertXmlToPdf } from '../features/converter/converterApi'
import { getApiErrorDetail } from '../api/client'

type Status = 'idle' | 'converting' | 'done'

export function ConverterPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [downloadName, setDownloadName] = useState('converted.pdf')

  // Освобождаем object URL при смене файла и размонтировании страницы.
  useEffect(() => {
    if (!pdfUrl) return
    return () => URL.revokeObjectURL(pdfUrl)
  }, [pdfUrl])

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    setFileName(file.name)
    setError(null)
    setPdfUrl(null)
    setStatus('converting')

    try {
      const result = await convertXmlToPdf(file)
      setPdfUrl(URL.createObjectURL(result.blob))
      setDownloadName(result.filename)
      setStatus('done')
    } catch (e) {
      setError(getApiErrorDetail(e))
      setStatus('idle')
    }
  }

  const handleDownload = () => {
    if (!pdfUrl) return
    const anchor = document.createElement('a')
    anchor.href = pdfUrl
    anchor.download = downloadName
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  }

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Конвертер XML → PDF</Typography>
      <Typography variant="body2" color="text.secondary">
        Загрузите XML-выписку Росреестра — получите официальный PDF-документ.
      </Typography>

      <input
        ref={inputRef}
        type="file"
        accept=".xml,application/xml,text/xml"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      {status !== 'done' && (
        <Box>
          <Button
            variant="contained"
            size="large"
            onClick={() => inputRef.current?.click()}
            disabled={status === 'converting'}
            startIcon={
              status === 'converting' ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <CloudUploadIcon />
              )
            }
          >
            {status === 'converting' ? 'Конвертация…' : 'Загрузить файл'}
          </Button>
          {status === 'converting' && fileName && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Конвертируем {fileName}…
            </Typography>
          )}
        </Box>
      )}

      {error && <Alert severity="error">{error}</Alert>}

      {status === 'done' && pdfUrl && (
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'center' }}>
            <Button variant="contained" startIcon={<DownloadIcon />} onClick={handleDownload}>
              Скачать PDF
            </Button>
            <Button
              variant="outlined"
              startIcon={<RestartAltIcon />}
              onClick={() => inputRef.current?.click()}
            >
              Загрузить другой файл
            </Button>
          </Stack>

          <Typography variant="body2" color="text.secondary">
            {fileName} → {downloadName}
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
