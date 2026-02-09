import { useState } from 'react'
import { Search, FileText, MessageSquare, Send, Loader2, X, Sparkles } from 'lucide-react'
import { searchDocuments, askQuestion } from '../services/api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState('semantic')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  // General chat state
  const [chatMode, setChatMode] = useState(false)
  const [chatMessages, setChatMessages] = useState([])

  // Document-focused chat state
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [docChatMessages, setDocChatMessages] = useState([])
  const [docChatQuery, setDocChatQuery] = useState('')
  const [docChatLoading, setDocChatLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      if (chatMode) {
        setChatMessages((prev) => [...prev, { role: 'user', content: query }])
        const response = await askQuestion(query)
        setChatMessages((prev) => [
          ...prev,
          { role: 'assistant', content: response.answer, sources: response.sources },
        ])
        setQuery('')
      } else {
        const response = await searchDocuments(query, searchType)
        setResults(response)
      }
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Handle opening document-focused chat
  const handleAskAboutDocument = (result) => {
    console.log('=== DEBUG: Ask About Document Clicked ===')
    console.log('Result object:', result)
    console.log('Document ID from result:', result.document_id)
    setSelectedDocument({
      id: result.document_id,
      filename: result.filename,
      page_number: result.page_number,
    })
    setDocChatMessages([])
    setDocChatQuery('')
  }

  // Handle document-focused chat question
  const handleDocChatSubmit = async (e) => {
    e.preventDefault()
    if (!docChatQuery.trim() || !selectedDocument) return

    console.log('=== DEBUG: Document Chat Submit ===')
    console.log('Selected Document:', selectedDocument)
    console.log('Document ID:', selectedDocument.id)
    console.log('Query:', docChatQuery)


    setDocChatLoading(true)
    setDocChatMessages((prev) => [...prev, { role: 'user', content: docChatQuery }])

    try {
      const response = await askQuestion(docChatQuery, 20, selectedDocument.id)
      setDocChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.answer, sources: response.sources },
      ])
      setDocChatQuery('')
    } catch (error) {
      console.error('Document chat error:', error)
      setDocChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '⚠️ Error: ' + error.message, sources: [] },
      ])
    } finally {
      setDocChatLoading(false)
    }
  }

  return (
    <div className="relative space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {chatMode ? 'Ask Questions' : 'Search Documents'}
          </h1>
          <p className="mt-1 text-gray-500">
            {chatMode
              ? 'Ask questions and get answers grounded in your documents.'
              : 'Search across all uploaded documents using semantic or keyword search.'}
          </p>
        </div>
        <button
          onClick={() => setChatMode(!chatMode)}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            chatMode
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          <span>{chatMode ? 'Chat Mode ON' : 'Enable Chat'}</span>
        </button>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={chatMode ? 'Ask a question about your documents...' : 'Search documents...'}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {!chatMode && (
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg bg-white text-sm"
          >
            <option value="semantic">Semantic</option>
            <option value="keyword">Keyword</option>
            <option value="hybrid">Hybrid</option>
          </select>
        )}

        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          <span>{chatMode ? 'Ask' : 'Search'}</span>
        </button>
      </form>

      {/* Chat Messages */}
      {chatMode && chatMessages.length > 0 && (
        <div className="space-y-4">
          {chatMessages.map((msg, i) => (
            <div
              key={i}
              className={`p-4 rounded-lg ${
                msg.role === 'user' ? 'bg-blue-50 ml-12' : 'bg-white border mr-12'
              }`}
            >
              <p className="text-sm font-medium text-gray-500 mb-1">
                {msg.role === 'user' ? 'You' : 'Assistant'}
              </p>
              <p className="text-gray-900 whitespace-pre-wrap">{msg.content}</p>
              {msg.sources?.length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs font-medium text-gray-500 mb-2">
                    Sources ({msg.sources.length} documents):
                  </p>
                  <div className="max-h-48 overflow-y-auto space-y-1">
                    {msg.sources.map((s, j) => (
                      <div key={j} className="text-xs text-gray-500">
                        📄 {s.filename} (Page {s.page_number}, Score: {s.score})
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Search Results */}
      {!chatMode && results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              {results.total_results} results for "{results.query}"
            </h2>
            <span className="text-sm text-gray-500">Search type: {results.search_type}</span>
          </div>

          {results.results.map((result, i) => (
            <div key={i} className="bg-white rounded-lg shadow border p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4 text-blue-500" />
                  <span className="font-medium text-gray-900">{result.filename}</span>
                  <span className="text-xs text-gray-400">Page {result.page_number}</span>
                  {result.extraction_method && (
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        result.extraction_method === 'digital'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-orange-100 text-orange-700'
                      }`}
                    >
                      {result.extraction_method}
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-mono text-gray-500">
                    Score: {result.score}
                  </span>
                  {/* Ask AI Button */}
                  <button
                    onClick={() => handleAskAboutDocument(result)}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-md hover:from-purple-700 hover:to-blue-700 text-xs font-medium transition-all"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Ask AI</span>
                  </button>
                </div>
              </div>
              <p className="mt-2 text-sm text-gray-700 leading-relaxed">
                {result.chunk_text}
              </p>
              {/* Entities found in this snippet */}
              {result.entities?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {result.entities.slice(0, 6).map((ent, j) => (
                    <span
                      key={j}
                      className="text-xs px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded"
                      title={ent.label}
                    >
                      {ent.label}: {ent.text}
                    </span>
                  ))}
                  {result.entities.length > 6 && (
                    <span className="text-xs text-gray-400">+{result.entities.length - 6} more</span>
                  )}
                </div>
              )}
            </div>
          ))}

          {results.total_results === 0 && (
            <div className="text-center py-12 text-gray-500">
              <Search className="mx-auto h-12 w-12 text-gray-300" />
              <p className="mt-4">No results found. Try a different query or upload more documents.</p>
            </div>
          )}
        </div>
      )}

      {/* Document-Focused Chat Side Panel */}
      {selectedDocument && (
        <div className="fixed inset-y-0 right-0 w-[480px] bg-white shadow-2xl border-l flex flex-col z-50 animate-slide-in">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Ask about this document</h2>
              </div>
              <p className="text-xs text-purple-100 mt-1 truncate">
                📄 {selectedDocument.filename}
              </p>
            </div>
            <button
              onClick={() => setSelectedDocument(null)}
              className="p-1 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Chat Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {docChatMessages.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare className="mx-auto h-12 w-12 text-gray-300" />
                <p className="mt-4 text-sm text-gray-500">
                  Ask questions about this document.<br />
                  I'll answer using only this document's content.
                </p>
              </div>
            ) : (
              docChatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-blue-100 ml-8'
                      : 'bg-white border shadow-sm'
                  }`}
                >
                  <p className="text-xs font-medium text-gray-500 mb-1">
                    {msg.role === 'user' ? 'You' : 'AI Assistant'}
                  </p>
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">{msg.content}</p>
                  {msg.sources?.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-500 mb-1">
                        📍 {msg.sources.length} relevant sections found
                      </p>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {msg.sources.map((s, j) => (
                          <div key={j} className="text-xs text-gray-500">
                            Page {s.page_number} • Score: {s.score}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Input Area */}
          <div className="border-t bg-white p-4">
            <form onSubmit={handleDocChatSubmit} className="flex gap-2">
              <input
                type="text"
                value={docChatQuery}
                onChange={(e) => setDocChatQuery(e.target.value)}
                placeholder="Ask about this document..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm"
                disabled={docChatLoading}
              />
              <button
                type="submit"
                disabled={docChatLoading || !docChatQuery.trim()}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 flex items-center space-x-1"
              >
                {docChatLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </form>
            <p className="text-xs text-gray-500 mt-2">
              💡 Answers are based only on: <span className="font-medium">{selectedDocument.filename}</span>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}