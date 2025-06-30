import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { FluentProvider, teamsLightTheme } from '@fluentui/react-components'
import Layout from './components/Layout/Layout'
import Dashboard from './components/Dashboard/Dashboard'
import FileExplorer from './components/FileExplorer/FileExplorer'
import Search from './components/Search/Search'
import Upload from './components/Upload/Upload'
import './App.css'

function App() {
  return (
    <FluentProvider theme={teamsLightTheme}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Search />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/disks/:diskId" element={<FileExplorer />} />
            <Route path="/disks/:diskId/browse/*" element={<FileExplorer />} />
            <Route path="/search" element={<Search />} />
            <Route path="/upload" element={<Upload />} />
          </Routes>
        </Layout>
      </Router>
    </FluentProvider>
  )
}

export default App