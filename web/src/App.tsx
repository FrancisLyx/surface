import { ConfigProvider, theme } from 'antd'
import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import AdminLayout from './layouts/AdminLayout'
import LoginPage from './pages/user/LoginPage'
import RegisterPage from './pages/user/RegisterPage'
import { appRoutes, defaultRoutePath } from './utils/route'
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
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AdminLayout />}>
            <Route index element={<Navigate to={defaultRoutePath} replace />} />
            {appRoutes.map((route) => {
              const Page = route.component
              return <Route key={route.path} path={route.path} element={<Page />} />
            })}
          </Route>
        </Route>
        <Route path="*" element={<Navigate to={defaultRoutePath} replace />} />
      </Routes>
    </ConfigProvider>
  )
}

export default App
