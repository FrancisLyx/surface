import { ConfigProvider, theme } from 'antd'
import { Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './layouts/AdminLayout'
import FundDetailPage from './pages/funds/FundDetailPage'
import FundEstimationsPage from './pages/funds/FundEstimationsPage'
import FundListPage from './pages/funds/FundListPage'
import FundValuePage from './pages/funds/FundValuePage'
import './App.css'

function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          borderRadius: 6,
          colorPrimary: '#1677ff',
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        },
      }}
    >
      <Routes>
        <Route element={<AdminLayout />}>
          <Route index element={<Navigate to="/funds" replace />} />
          <Route path="/funds" element={<FundListPage />} />
          <Route path="/funds/estimations" element={<FundEstimationsPage />} />
          <Route path="/funds/detail" element={<FundDetailPage />} />
          <Route path="/funds/value" element={<FundValuePage />} />
          <Route path="*" element={<Navigate to="/funds" replace />} />
        </Route>
      </Routes>
    </ConfigProvider>
  )
}

export default App
