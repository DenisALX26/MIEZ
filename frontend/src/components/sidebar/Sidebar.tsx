import { useEffect, useMemo, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  FiBell,
  FiChevronDown,
  FiGrid,
  FiLogOut,
  FiMenu,
  FiSettings,
  FiUserPlus,
  FiFileText,
  FiZap,
} from 'react-icons/fi'
import { useAuth } from '../../context/AuthContext'

const SIDEBAR_COLLAPSED_KEY = 'miez.sidebar.collapsed'

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/dashboard', icon: FiGrid },
  { label: 'Employees', to: '/employees', icon: FiUserPlus },
  { label: 'Reports', to: '/reports', icon: FiFileText },
  { label: 'Workflows', to: '/workflows', icon: FiZap },
]

const Sidebar = () => {
  const { logout, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const unreadCount = 4

  useEffect(() => {
    const storedState = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
    if (storedState !== null) {
      setIsCollapsed(storedState === 'true')
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(isCollapsed))
  }, [isCollapsed])

  const pageTitle = useMemo(() => {
    const active = NAV_ITEMS.find(item => location.pathname.startsWith(item.to))
    return active?.label ?? 'Module'
  }, [location.pathname])

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${isCollapsed ? 'is-collapsed' : ''}`}>
        <div className="sidebar-header">
          {!isCollapsed && <span className="brand-name">MIEZ Portal</span>}
          <button
            className="hamburger-btn"
            type="button"
            onClick={() => setIsCollapsed(current => !current)}
            aria-label="Toggle sidebar"
          >
            <FiMenu aria-hidden="true" />
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {NAV_ITEMS.map(item => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <Icon aria-hidden="true" />
                {!isCollapsed && <span>{item.label}</span>}
              </NavLink>
            )
          })}

        </nav>

        <div className="sidebar-footer">
          <NavLink
            to="/settings"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <FiSettings aria-hidden="true" />
            {!isCollapsed && <span>Settings</span>}
          </NavLink>

          <button className="nav-link logout-btn" type="button" onClick={handleLogout}>
            <FiLogOut aria-hidden="true" />
            {!isCollapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>

      <div className="shell-main">
        <header className="top-bar">
          <h1>{pageTitle}</h1>
          <div className="topbar-right">
            <span className="role-chip">{user?.role ?? 'User'}</span>
            <button className="notification-btn" type="button" aria-label="Notifications">
              <FiBell aria-hidden="true" />
              {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
            </button>
          </div>
        </header>

        <main className="content-area">
          <Outlet />
        </main>
      </div>

      <button className="assistant-fab" type="button" aria-label="Open MIEZ Assistant">
        MIEZ Assistant
        <FiChevronDown aria-hidden="true" />
      </button>
    </div>
  )
}

export default Sidebar