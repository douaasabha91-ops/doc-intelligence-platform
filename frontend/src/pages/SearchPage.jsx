import { useState } from 'react'
import { Search, FileText, MessageSquare, Send, Loader2 } from 'lucide-react'
import { searchDocuments, askQuestion } from '../services/api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState('semantic')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  // Chat state
  const [chatMode, setChatMode] = useState(false)
  const [chatMessages, setChatMessages] = useState([])

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

  return (
    <div className="space-y-6">
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
                  <p className="text-xs font-medium text-gray-500 mb-2">Sources:</p>
                  {msg.sources.slice(0, 3).map((s, j) => (
                    <div key={j} className="text-xs text-gray-500">
                      📄 {s.filename} (Page {s.page_number}, Score: {s.score})
                    </div>
                  ))}
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
                <span className="text-sm font-mono text-gray-500">
                  Score: {result.score}
                </span>
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
    </div>
  )
}
