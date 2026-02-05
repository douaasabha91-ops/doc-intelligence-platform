import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Eye, Layers, Cpu, Tag } from 'lucide-react'
import { uploadDocument } from '../services/api'

export default function UploadPage() {
  const [uploads, setUploads] = useState([])
  const [processing, setProcessing] = useState(false)

  const onDrop = useCallback(async (acceptedFiles) => {
    for (const file of acceptedFiles) {
      const ext = file.name.split('.').pop().toLowerCase()
      const allowed = ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp']
      if (!allowed.includes(ext)) continue

      setProcessing(true)
      const uploadEntry = {
        id: Date.now(),
        filename: file.name,
        status: 'processing',
        result: null,
      }
      setUploads((prev) => [uploadEntry, ...prev])

      try {
        const result = await uploadDocument(file)
        setUploads((prev) =>
          prev.map((u) =>
            u.id === uploadEntry.id ? { ...u, status: 'success', result } : u
          )
        )
      } catch (error) {
        setUploads((prev) =>
          prev.map((u) =>
            u.id === uploadEntry.id
              ? { ...u, status: 'error', result: { message: error.message } }
              : u
          )
        )
      } finally {
        setProcessing(false)
      }
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/tiff': ['.tiff', '.tif'],
      'image/bmp': ['.bmp'],
      'image/webp': ['.webp'],
    },
    multiple: true,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Documents</h1>
        <p className="mt-1 text-gray-500">
          Upload PDFs or scanned images (JPG, PNG, TIFF) to extract text via OCR, identify entities, and enable semantic search.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 bg-white'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-4 text-lg font-medium text-gray-700">
          {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
        </p>
        <p className="mt-1 text-sm text-gray-500">PDF, JPG, PNG, TIFF, BMP — or click to browse</p>
      </div>

      {/* Upload Results */}
      {uploads.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Processing Results</h2>
          {uploads.map((upload) => (
            <div key={upload.id} className="bg-white rounded-lg shadow p-4 border">
              <div className="flex items-start space-x-3">
                {upload.status === 'processing' && (
                  <Loader2 className="h-5 w-5 text-blue-500 animate-spin mt-0.5" />
                )}
                {upload.status === 'success' && (
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                )}
                {upload.status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                )}
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-gray-400" />
                    <span className="font-medium text-gray-900">{upload.filename}</span>
                  </div>

                  {upload.status === 'processing' && (
                    <p className="mt-1 text-sm text-blue-600">
                      Pipeline: Image Enhancement → OCR → NER → Embeddings → Storage...
                    </p>
                  )}

                  {upload.status === 'success' && upload.result && (
                    <div className="mt-2 space-y-2">
                      <p className="text-sm text-green-700">{upload.result.message}</p>

                      {/* Summary Stats */}
                      <div className="flex flex-wrap gap-3 text-xs">
                        <span className="px-2 py-1 bg-gray-100 rounded text-gray-600">
                          ID: {upload.result.id}
                        </span>
                        <span className="px-2 py-1 bg-blue-50 rounded text-blue-700">
                          📄 {upload.result.page_count} pages
                        </span>
                        <span className="px-2 py-1 bg-purple-50 rounded text-purple-700">
                          🧩 {upload.result.total_chunks} chunks
                        </span>
                        <span className="px-2 py-1 bg-green-50 rounded text-green-700">
                          ✅ {upload.result.status}
                        </span>
                      </div>

                      {/* 1. Extracted Text Preview */}
                      <details className="mt-2">
                        <summary className="text-sm text-blue-600 cursor-pointer flex items-center gap-1">
                          <Eye className="h-3.5 w-3.5" /> View extracted text preview
                        </summary>
                        <pre className="mt-1 text-xs text-gray-600 bg-gray-50 p-3 rounded max-h-40 overflow-y-auto whitespace-pre-wrap">
                          {upload.result.extracted_text_preview}
                        </pre>
                      </details>

                      {/* 2. Named Entities (NER) */}
                      {upload.result.entities?.length > 0 && (
                        <details className="mt-2">
                          <summary className="text-sm text-emerald-600 cursor-pointer flex items-center gap-1">
                            <Tag className="h-3.5 w-3.5" /> Named entities ({upload.result.entities.length} types found)
                          </summary>
                          <div className="mt-2 space-y-2">
                            {upload.result.entities.map((ent, i) => (
                              <div key={i} className="flex items-start gap-2">
                                <span className="text-xs font-semibold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded whitespace-nowrap">
                                  {ent.label}
                                </span>
                                <div className="flex flex-wrap gap-1">
                                  {ent.values?.slice(0, 8).map((v, j) => (
                                    <span key={j} className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded">
                                      {v}
                                    </span>
                                  ))}
                                  {ent.values?.length > 8 && (
                                    <span className="text-xs text-gray-400">+{ent.values.length - 8} more</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}

                      {/* 3. Extraction Methods + Layout + Preprocessing Pipeline */}
                      {upload.result.extraction_details?.length > 0 && (
                        <details className="mt-2">
                          <summary className="text-sm text-purple-600 cursor-pointer flex items-center gap-1">
                            <Layers className="h-3.5 w-3.5" /> Extraction details per page (OCR pipeline + layout)
                          </summary>
                          <div className="mt-2 space-y-4">
                            {upload.result.extraction_details.map((detail, i) => (
                              <div key={i} className="border rounded-lg p-3 bg-gray-50">
                                {/* Page Header */}
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-gray-700">
                                      Page {detail.page}
                                    </span>
                                    {detail.block_count > 0 && (
                                      <span className="text-xs px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded">
                                        {detail.block_count} text blocks
                                      </span>
                                    )}
                                  </div>
                                  <span
                                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                      detail.primary_method === 'digital'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-orange-100 text-orange-700'
                                    }`}
                                  >
                                    {detail.primary_method === 'digital' ? '📄 Digital (PyMuPDF)' : '🔍 OCR (Tesseract)'}
                                  </span>
                                </div>

                                {/* Digital vs OCR Comparison */}
                                {detail.has_digital && detail.has_ocr && (
                                  <div className="grid grid-cols-2 gap-3 mb-3">
                                    <div>
                                      <p className="text-xs font-medium text-green-700 mb-1">📄 Digital extraction</p>
                                      <pre className="text-xs text-gray-600 bg-white p-2 rounded max-h-20 overflow-y-auto whitespace-pre-wrap border">
                                        {detail.digital_preview || 'No text'}
                                      </pre>
                                    </div>
                                    <div>
                                      <p className="text-xs font-medium text-orange-700 mb-1">🔍 OCR extraction</p>
                                      <pre className="text-xs text-gray-600 bg-white p-2 rounded max-h-20 overflow-y-auto whitespace-pre-wrap border">
                                        {detail.ocr_preview || 'No text'}
                                      </pre>
                                    </div>
                                  </div>
                                )}

                                {/* Preprocessing Pipeline Visualization */}
                                {detail.preprocessing_steps && (
                                  <details className="mt-2">
                                    <summary className="text-xs text-orange-600 cursor-pointer flex items-center gap-1">
                                      <Cpu className="h-3 w-3" /> View image preprocessing pipeline
                                    </summary>
                                    <div className="mt-2 grid grid-cols-3 gap-2">
                                      {Object.entries(detail.preprocessing_steps).map(([step, base64]) => (
                                        <div key={step} className="text-center">
                                          <img
                                            src={`data:image/jpeg;base64,${base64}`}
                                            alt={step}
                                            className="rounded border w-full"
                                          />
                                          <p className="text-xs text-gray-500 mt-1 capitalize">
                                            {step.replace('_', ' ')}
                                          </p>
                                        </div>
                                      ))}
                                    </div>
                                  </details>
                                )}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  )}

                  {upload.status === 'error' && (
                    <p className="mt-1 text-sm text-red-600">
                      Error: {upload.result?.message || 'Upload failed'}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
