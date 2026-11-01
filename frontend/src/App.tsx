import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Overview from './pages/Overview'
import Chat from './pages/Chat'
import Documents from './pages/Documents'
import Companies from './pages/Companies'
import CompanyDetail from './pages/CompanyDetail'
import Analytics from './pages/Analytics'
import RAGExplorerPage from './pages/RAGExplorerPage'
import PolicyPage from './pages/PolicyPage'
import Settings from './pages/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/companies/:id" element={<CompanyDetail />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/rag-explorer" element={<RAGExplorerPage />} />
          <Route path="/policy" element={<PolicyPage />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

