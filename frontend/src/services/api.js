import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for large PDF processing
})

// ── Document Endpoints ──

export const uploadDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const listDocuments = async () => {
  const response = await api.get('/documents/')
  return response.data
}

export const getStats = async () => {
  const response = await api.get('/documents/stats')
  return response.data
}

export const deleteDocument = async (docId) => {
  const response = await api.delete(`/documents/${docId}`)
  return response.data
}

// ── Search Endpoints ──

export const searchDocuments = async (query, searchType = 'semantic', topK = 10) => {
  const response = await api.post('/search/', {
    query,
    search_type: searchType,
    top_k: topK,
  })
  return response.data
}

// ── Chat Endpoint ──

export const askQuestion = async (question, topK = 20) => {
  const response = await api.post('/chat/', {
    question,
    top_k: topK,
  })
  return response.data
}

export default api
