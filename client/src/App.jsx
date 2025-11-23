import { Routes, Route, Link, useParams } from 'react-router-dom'

function HomePage() {
  return (
    <div style={{ padding: '1.5rem' }}>
      <h1>Heathgate Drone Image Viewer</h1>
      <p>Welcome. Choose a project to begin.</p>
    </div>
  )
}

function ProjectsPage() {
  return (
    <div style={{ padding: '1.5rem' }}>
      <h1>Projects</h1>
      <p>List of drone image projects will go here.</p>
    </div>
  )
}

function ViewerPage() {
  const { id } = useParams()
  return (
    <div style={{ padding: '1.5rem' }}>
      <h1>Viewer</h1>
      <p>Showing viewer for project/image ID: {id}</p>
    </div>
  )
}

function NotFoundPage() {
  return (
    <div style={{ padding: '1.5rem' }}>
      <h1>404 - Not Found</h1>
      <p>The page you’re looking for does not exist.</p>
    </div>
  )
}

function App() {
  return (
    <div>
      <nav
        style={{
          padding: '1rem 1.5rem',
          borderBottom: '1px solid #ddd',
          marginBottom: '1rem',
        }}
      >
        <Link to="/" style={{ marginRight: '1rem' }}>Home</Link>
        <Link to="/projects" style={{ marginRight: '1rem' }}>Projects</Link>
        <Link to="/viewer/123">Sample Viewer</Link>
      </nav>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/viewer/:id" element={<ViewerPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  )
}

export default App

