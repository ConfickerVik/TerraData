import { Box, Chip, Stack, Typography } from '@mui/material'

interface PagePlaceholderProps {
  title: string
  description: string
}

export function PagePlaceholder({ title, description }: PagePlaceholderProps) {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">{title}</Typography>
      <Box>
        <Chip label="В разработке" color="warning" size="small" />
      </Box>
      <Typography color="text.secondary">{description}</Typography>
    </Stack>
  )
}
