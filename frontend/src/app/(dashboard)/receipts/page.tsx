'use client'

import { useState } from 'react'
import api from '@/lib/api'

export default function ReceiptsPage() {
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [uploading, setUploading] = useState(false)

  const onFile = async (file: File) => {
    const url = URL.createObjectURL(file)
    setPreview(url)
    const form = new FormData()
    form.append('file', file)
    setUploading(true)
    try {
      const res = await api.post('/api/ocr/receipt', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResult(res.data)
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (ev: React.DragEvent<HTMLDivElement>) => {
    ev.preventDefault()
    const file = ev.dataTransfer.files?.[0]
    if (file) onFile(file)
  }

  const onCapture = async (ev: React.ChangeEvent<HTMLInputElement>) => {
    const file = ev.target.files?.[0]
    if (file) onFile(file)
  }

  return (
    <div className="space-y-4">
      <div className="text-xl font-semibold">Receipt OCR</div>
      <div
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        className="grid place-items-center h-40 rounded-lg border border-dashed text-sm text-muted-foreground"
      >
        Drag & drop receipt image here
      </div>
      <div className="flex items-center gap-2">
        <label className="rounded-md border px-3 py-2 text-sm cursor-pointer">
          Upload Image
          <input type="file" accept="image/*" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f) }} />
        </label>
        <label className="rounded-md border px-3 py-2 text-sm cursor-pointer">
          Camera
          <input type="file" accept="image/*" capture="environment" className="hidden" onChange={onCapture} />
        </label>
      </div>

      {uploading && <div className="text-sm text-muted-foreground">Processing…</div>}

      {preview && (
        <div className="grid gap-3 md:grid-cols-2">
          <img src={preview} alt="preview" className="rounded-lg border" />
          <div className="rounded-lg border p-3 space-y-2 text-sm">
            <div className="font-medium">Parsed Result</div>
            {result ? (
              <div className="space-y-1">
                <div>Merchant: <span className="text-foreground">{result.merchant || '-'}</span></div>
                <div>Total: <span className="text-foreground">{result.total_amount ?? '-'}</span></div>
                <div>Date: <span className="text-foreground">{result.date || '-'}</span></div>
                <div className="text-xs text-muted-foreground break-all">URL: {result.s3_url}</div>
                <details className="mt-2">
                  <summary className="cursor-pointer">Raw Text</summary>
                  <pre className="whitespace-pre-wrap text-xs mt-2">{result.text}</pre>
                </details>
              </div>
            ) : (
              <div className="text-muted-foreground">No result yet</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


