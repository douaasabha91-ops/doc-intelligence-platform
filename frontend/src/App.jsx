import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import { FileText, Search, MessageSquare, BarChart3 } from 'lucide-react'
import UploadPage from './pages/UploadPage'
import SearchPage from './pages/SearchPage'
import DocumentView from './pages/DocumentView'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-8">
                <div className="flex items-center space-x-2">
                  <FileText className="h-6 w-6 text-blue-600" />
                  <span className="text-xl font-bold text-gray-900">DocIntel</span>
                </div>
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-gray-900'
                    }`
                  }
                >
                  <FileText className="h-4 w-4" />
                  <span>Upload</span>
                </NavLink>
                <NavLink
                  to="/search"
                  className={({ isActive }) =>
                    `flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive ? 'text-blue-600 bg-blue-50' : 'text-gray-600 hover:text-gray-900'
                    }`
                  }
                >
                  <Search className="h-4 w-4" />
                  <span>Search</span>
                </NavLink>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/document/:id" element={<DocumentView />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
