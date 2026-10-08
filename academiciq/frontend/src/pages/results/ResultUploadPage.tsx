/**
 * ResultUploadPage — drag-and-drop PDF upload with real-time status.
 * File validation: PDF only, size limit shown, duplicate hash detection.
 */
import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/PageHeader'
import { resultsApi } from '@/api/endpoints'
import type { ResultUpload } from '@/types'

const MAX_MB = 50

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function ResultUploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ResultUpload | null>(null)

  const handleFile = (f: File) => {
    setError(null)
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are accepted.')
      return
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`File size exceeds ${MAX_MB} MB limit.`)
      return
    }
    setFile(f)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const { data } = await resultsApi.upload(form)
      setResult(data)
    } catch (err: any) {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        'Upload failed. Please try again.'
      setError(msg)
    } finally {
      setUploading(false)
    }
  }

  if (result) {
    return (
      <div className="space-y-4">
        <PageHeader title="Upload Queued" />
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-sm text-green-800">
          <p className="font-semibold text-base mb-1">✓ Upload accepted</p>
          <p>Upload ID: <code className="font-mono text-xs">{result.id}</code></p>
          <p className="mt-1">Status: <strong>{result.processing_status}</strong></p>
          <p className="mt-1 text-xs text-green-600">
            The PDF is now being processed in the background. You will be able to review
            the extracted records before committing to the database.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => navigate(`/results/uploads/${result.id}`)}
            className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            View upload status
          </button>
          <button
            onClick={() => { setFile(null); setResult(null) }}
            className="px-4 py-2 border border-gray-300 text-sm rounded-lg text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            Upload another
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Result PDF"
        subtitle="Upload a university result PDF. The file will be processed in the background."
      />

      {error && (
        <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload PDF — click or drag and drop"
        onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors
          focus:outline-none focus:ring-2 focus:ring-primary-500
          ${dragOver ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-300 hover:bg-gray-50'}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          aria-hidden="true"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        />
        <p className="text-4xl mb-3" aria-hidden="true">📄</p>
        {file ? (
          <div>
            <p className="font-medium text-gray-800">{file.name}</p>
            <p className="text-sm text-gray-500 mt-1">{formatBytes(file.size)}</p>
          </div>
        ) : (
          <div>
            <p className="font-medium text-gray-700">Click to select or drag a PDF here</p>
            <p className="text-sm text-gray-400 mt-1">PDF only · Max {MAX_MB} MB</p>
          </div>
        )}
      </div>

      {/* Notes */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-xs text-yellow-800 space-y-1">
        <p className="font-semibold">Before uploading:</p>
        <ul className="list-disc list-inside space-y-0.5 text-yellow-700">
          <li>Duplicate files (same SHA-256 hash) are detected and blocked.</li>
          <li>Extracted records go to a staging area — nothing is committed without your review.</li>
          <li>All extractions carry page numbers and confidence scores for provenance.</li>
          <li>Low-confidence OCR fields are flagged for human review.</li>
        </ul>
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="px-6 py-2.5 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? 'Uploading…' : 'Upload PDF'}
      </button>
    </div>
  )
}
