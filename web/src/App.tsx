import { ConfigProvider, theme } from 'antd'
import { Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './layouts/AdminLayout'
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
        <Route element={<AdminLayout />}>
          <Route index element={<Navigate to={defaultRoutePath} replace />} />
          {appRoutes.map((route) => {
            const Page = route.component
            return <Route key={route.path} path={route.path} element={<Page />} />
          })}
          <Route path="*" element={<Navigate to={defaultRoutePath} replace />} />
        </Route>
      </Routes>
    </ConfigProvider>
  )
}

export default App
