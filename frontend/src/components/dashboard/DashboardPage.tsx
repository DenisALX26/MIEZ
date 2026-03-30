import { useEffect, useMemo, useState } from 'react'
import {
  FiMonitor,
  FiUsers,
  FiBarChart2,
  FiPackage,
  FiHome,
  FiTrash2,
  FiPlus,
} from 'react-icons/fi'
import { useAuth } from '../../context/AuthContext'

type Department = {
  id: number
  name: string
  slug: string
  icon?: string
}

const iconMap = {
  Monitor: FiMonitor,
  Users: FiUsers,
  BarChart3: FiBarChart2,
  Package: FiPackage,
  Building2: FiHome,
} as const

const DashboardPage = () => {
  const { user } = useAuth()
  const [departments, setDepartments] = useState<Department[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [icon, setIcon] = useState('Building2')

  useEffect(() => {
    const fetchDepartments = async () => {
      if (user?.role !== 'CEO') {
        setDepartments([])
        setIsLoading(false)
        return
      }

      try {
        const response = await fetch('/api/departments/', {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`Failed to load departments: ${response.status}`)
        }

        const data = (await response.json()) as Department[]
        setDepartments(data)
        window.dispatchEvent(new CustomEvent('departments-updated', { detail: data }))
      } catch (error) {
        console.error('Eroare la incarcarea departamentelor', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDepartments()
  }, [user?.role])

  const handleDelete = async (id: number) => {
    try {
      const response = await fetch(`/api/departments/${id}/`, {
        method: 'DELETE',
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error(`Failed to delete department: ${response.status}`)
      }

      setDepartments(current => {
        const next = current.filter(dep => dep.id !== id)
        window.dispatchEvent(new CustomEvent('departments-updated', { detail: next }))
        return next
      })
    } catch (error) {
      console.error('Eroare la stergere', error)
    }
  }

  const toSlug = (value: string) =>
    value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const payload = {
      name: name.trim(),
      slug: slug.trim() || toSlug(name),
      icon,
    }

    if (!payload.name || !payload.slug) {
      return
    }

    try {
      const response = await fetch('/api/departments/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(`Failed to create department: ${response.status}`)
      }

      const createdDepartment = (await response.json()) as Department

      setDepartments(current => {
        const next = [...current, createdDepartment].sort((a, b) => a.name.localeCompare(b.name))
        window.dispatchEvent(new CustomEvent('departments-updated', { detail: next }))
        return next
      })
      setName('')
      setSlug('')
      setIcon('Building2')
    } catch (error) {
      console.error('Eroare la creare', error)
    }
  }

  const stats = useMemo(() => {
    return [
      { label: 'Departments', value: departments.length },
      { label: 'Employee Teams', value: departments.length },
      { label: 'Pending Actions', value: departments.length === 0 ? 1 : 0 },
    ]
  }, [departments])

  if (isLoading) {
    return <div className="module-card">Loading...</div>
  }

  if (user?.role !== 'CEO') {
    return (
      <section className="module-card">
        <h2>Dashboard</h2>
        <p>Department management is only available for CEO accounts.</p>
      </section>
    )
  }

  return (
    <div className="dashboard-wrap">
      <div className="dashboard-header-row">
        <div>
          <h2>Department Management</h2>
          <p>Add or remove departments to customize your organization</p>
        </div>
      </div>

      <form className="department-form" onSubmit={handleCreate}>
        <input
          value={name}
          onChange={event => setName(event.target.value)}
          placeholder="Department name"
          aria-label="Department name"
        />
        <input
          value={slug}
          onChange={event => setSlug(event.target.value)}
          placeholder="Slug (optional)"
          aria-label="Department slug"
        />
        <select value={icon} onChange={event => setIcon(event.target.value)} aria-label="Department icon">
          <option value="Building2">Building</option>
          <option value="Monitor">IT</option>
          <option value="Users">HR</option>
          <option value="BarChart3">Sales</option>
          <option value="Package">Inventory</option>
        </select>
        <button type="submit">
          <FiPlus />
          Add Department
        </button>
      </form>

      <div className="stats-grid">
        {stats.map(stat => (
          <article key={stat.label} className="stat-card">
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
          </article>
        ))}
      </div>

      {departments.length === 0 ? (
        <section className="empty-state-card">
          <div className="empty-state-icon">
            <FiHome />
          </div>
          <h3>No Departments Added</h3>
          <p>
            Get started by adding your first department. Each department will unlock
            specialized tools and views for your team.
          </p>
        </section>
      ) : (
        <section className="department-grid">
          {departments.map(dep => {
            const Icon = iconMap[(dep.icon as keyof typeof iconMap) ?? 'Building2'] ?? FiHome
            return (
              <article key={dep.id} className="department-card">
                <div className="department-card-top">
                  <div className="department-icon-wrap">
                    <Icon />
                  </div>
                  <button
                    type="button"
                    className="delete-btn"
                    onClick={() => handleDelete(dep.id)}
                    aria-label={`Delete ${dep.name}`}
                  >
                    <FiTrash2 />
                  </button>
                </div>

                <h4>{dep.name}</h4>
                <p>{`Module path: /departments/${dep.slug}`}</p>
              </article>
            )
          })}
        </section>
      )}
    </div>
  )
}

export default DashboardPage