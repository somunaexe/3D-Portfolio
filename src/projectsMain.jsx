import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import ProjectsExplorer from './pages/ProjectsExplorer.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ProjectsExplorer />
  </StrictMode>,
)
