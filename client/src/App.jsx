import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import ImageViewerPage from './pages/ImageViewerPage.jsx'
import ClusterViewerPage from './pages/ClusterViewerPage.jsx'
import ImageAdminPage from './pages/ImageAdminPage.jsx'

function App() {
  return (
    <div>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/image/:id" element={<ImageViewerPage />} />
        <Route path="/cluster/:cluster_id" element={<ClusterViewerPage />} />
        <Route path="/admin" element={<ImageAdminPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  )
}

export default App

