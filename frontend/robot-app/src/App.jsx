import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import TableView from '@/pages/TableView'
import FormView from '@/pages/FormView'
import ControllerView from '@/pages/ControllerView'
import ProcessView from '@/pages/ProcessView'
import AboutView from '@/pages/AboutView'

function App() {
  const [activePage, setActivePage] = useState('table')

  const renderPage = () => {
    switch (activePage) {
      case 'table':
        return <TableView />
      case 'form':
        return <FormView />
      case 'controller':
        return <ControllerView />
      case 'process':
        return <ProcessView />
      case 'about':
        return <AboutView />
      default:
        return null
    }
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <Sidebar onSelect={setActivePage} active={activePage} />
      <main className="flex-1 p-6 overflow-auto">
        {renderPage()}
      </main>
    </div>
  )
}

export default App
