import { NavLink, Route, Routes } from 'react-router-dom'
import AgentPage from './pages/AgentPage'
import CategoriesPage from './pages/CategoriesPage'
import ImageGenPage from './pages/ImageGenPage'
import ItemsPage from './pages/ItemsPage'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>物品管理系统</h1>
        <p>分类 + 物品管理，AI 对话管家，以及文生图</p>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
            物品管理
          </NavLink>
          <NavLink
            to="/categories"
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            分类管理
          </NavLink>
          <NavLink
            to="/agent"
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            物品管家
          </NavLink>
          <NavLink
            to="/images"
            className={({ isActive }) => (isActive ? 'active' : '')}
          >
            文生图
          </NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<ItemsPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/agent" element={<AgentPage />} />
        <Route path="/images" element={<ImageGenPage />} />
      </Routes>
    </div>
  )
}

export default App
