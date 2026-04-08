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

const CeoDashboard = () => {
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
    return <div className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">Loading...</div>
  }

  if (user?.role !== 'CEO') {
    return (
      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
        <h2>Dashboard</h2>
        <p>Department management is only available for CEO accounts.</p>
      </section>
    )
  }

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <h2 className="text-[1.15rem] font-semibold">Department Management</h2>
        <p className="text-[0.92rem] text-[var(--muted-foreground)]">
          Add or remove departments to customize your organization
        </p>
      </header>

      <form className="grid grid-cols-[1.2fr_1fr_0.8fr_auto] gap-[0.6rem] bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-[0.9rem]" onSubmit={handleCreate}>
        <input
          className="min-h-[40px] border border-[var(--border)] rounded-[10px] px-[0.7rem] bg-[var(--input-background)] text-[var(--foreground)]"
          value={name}
          onChange={event => setName(event.target.value)}
          placeholder="Department name"
          aria-label="Department name"
        />
        <input
          className="min-h-[40px] border border-[var(--border)] rounded-[10px] px-[0.7rem] bg-[var(--input-background)] text-[var(--foreground)]"
          value={slug}
          onChange={event => setSlug(event.target.value)}
          placeholder="Slug (optional)"
          aria-label="Department slug"
        />
        <select className="min-h-[40px] border border-[var(--border)] rounded-[10px] px-[0.7rem] bg-[var(--input-background)] text-[var(--foreground)]" value={icon} onChange={event => setIcon(event.target.value)} aria-label="Department icon">
          <option value="Building2">Building</option>
          <option value="Monitor">IT</option>
          <option value="Users">HR</option>
          <option value="BarChart3">Sales</option>
          <option value="Package">Inventory</option>
        </select>
        <button className="min-h-[40px] rounded-[10px] bg-[var(--primary)] text-[var(--primary-foreground)] px-[0.9rem] font-bold cursor-pointer inline-flex items-center gap-[0.35rem] border-none" type="submit">
          <FiPlus />
          Add Department
        </button>
      </form>

      <div className="grid grid-cols-3 gap-4">
        {stats.map(stat => (
          <article key={stat.label} className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl px-[1.05rem] py-4 flex flex-col gap-[0.3rem]">
            <span className="text-[var(--muted-foreground)] text-[0.82rem]">{stat.label}</span>
            <strong className="text-[1.1rem]">{stat.value}</strong>
          </article>
        ))}
      </div>

      {departments.length === 0 ? (
        <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl px-[1.2rem] py-[2.2rem] min-h-[340px] flex flex-col items-center justify-center text-center gap-[0.7rem]">
          <div className="w-[54px] h-[54px] rounded-full border border-[var(--border)] bg-[var(--input-background)] grid place-items-center text-[var(--primary)]">
            <FiHome />
          </div>
          <h3>No Departments Added</h3>
          <p>
            Get started by adding your first department. Each department will unlock
            specialized tools and views for your team.
          </p>
        </section>
      ) : (
        <section className="grid grid-cols-4 gap-4">
          {departments.map(dep => {
            const Icon = iconMap[(dep.icon as keyof typeof iconMap) ?? 'Building2'] ?? FiHome
            return (
              <article key={dep.id} className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-4 flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="w-[44px] h-[44px] rounded-2xl bg-[var(--input-background)] text-[var(--primary)] grid place-items-center">
                    <Icon />
                  </div>
                  <button
                    type="button"
                    className="w-[34px] h-[34px] rounded-lg border border-[var(--border)] bg-transparent text-[var(--destructive)] grid place-items-center cursor-pointer hover:bg-[#d1353b14]"
                    onClick={() => handleDelete(dep.id)}
                    aria-label={`Delete ${dep.name}`}
                  >
                    <FiTrash2 />
                  </button>
                </div>

                <div className="flex flex-col gap-1">
                  <h4 className="font-semibold">{dep.name}</h4>
                  <p className="text-[0.9rem] text-[var(--muted-foreground)]">
                    {`Module path: /departments/${dep.slug}`}
                  </p>
                </div>
              </article>
            )
          })}
        </section>
      )}
    </div>
  )
}

export default CeoDashboard