import { NavLink, Route, Routes } from 'react-router-dom'
import CategoriesPage from './pages/CategoriesPage'
import ItemsPage from './pages/ItemsPage'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>物品管理系统</h1>
        <p>两张表：分类 categories + 物品 items（一对多关联）</p>
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
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<ItemsPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
      </Routes>
    </div>
  )
}

export default App
