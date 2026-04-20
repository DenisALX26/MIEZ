import { useEffect, useState } from 'react'
import { FiClock, FiDownload, FiFileText } from 'react-icons/fi'

interface Report {
  id: number
  name: string
  slug: string
  category: string
  period: string
  file_size_kb: number
  generated_at: string | null
  file_available: boolean
}

const CATEGORIES = ['All', 'Sales', 'Finance', 'Inventory', 'HR', 'IT']

const CATEGORY_COLOR: Record<string, string> = {
  Sales: 'text-blue-500',
  Finance: 'text-purple-500',
  Inventory: 'text-orange-400',
  HR: 'text-green-500',
  IT: 'text-yellow-500',
}

function formatSize(kb: number): string {
  if (kb >= 1000) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb} KB`
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [activeCategory, setActiveCategory] = useState('All')
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    const params = activeCategory !== 'All' ? `?category=${activeCategory}` : ''
    fetch(`/api/reports/${params}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => setReports(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false))
  }, [activeCategory])

  const handleDownload = async (report: Report) => {
    if (!report.file_available || downloading === report.id) return
    setDownloading(report.id)
    try {
      const res = await fetch(`/api/reports/${report.id}/download/`, { credentials: 'include' })
      if (!res.ok) { alert('File not available yet. Generate the report first.'); return }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${report.slug}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Category filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors cursor-pointer ${
              activeCategory === cat
                ? 'bg-[#D1353B] text-white border-[#D1353B]'
                : 'bg-white text-[var(--foreground)] border-[var(--border)] hover:border-[#D1353B] hover:text-[#D1353B]'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Table card */}
      <div className="bg-white border border-[var(--border)] rounded-2xl overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-4 border-b border-[var(--border)]">
          <FiClock className="text-[var(--muted-foreground)] w-4 h-4" />
          <span className="font-semibold text-sm">Available Reports</span>
        </div>

        {loading ? (
          <div className="py-16 text-center text-sm text-[var(--muted-foreground)]">Loading…</div>
        ) : reports.length === 0 ? (
          <div className="py-16 text-center text-sm text-[var(--muted-foreground)]">No reports found.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                {['Report Name', 'Category', 'Period', 'Size', 'Generated', 'Action'].map(col => (
                  <th key={col} className="px-5 py-3 text-left text-xs font-medium text-[var(--muted-foreground)]">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {reports.map(report => (
                <tr key={report.id} className="border-b border-[var(--border)] last:border-0 hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <FiFileText className="text-gray-400 w-4 h-4 shrink-0" />
                      <span className="font-medium text-[var(--foreground)]">{report.name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`text-xs font-semibold ${CATEGORY_COLOR[report.category] ?? 'text-gray-500'}`}>
                      {report.category}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-[var(--muted-foreground)]">{report.period}</td>
                  <td className="px-5 py-3.5 text-[var(--muted-foreground)]">{formatSize(report.file_size_kb)}</td>
                  <td className="px-5 py-3.5 text-[var(--muted-foreground)]">{formatDate(report.generated_at)}</td>
                  <td className="px-5 py-3.5">
                    <button
                      onClick={() => handleDownload(report)}
                      disabled={!report.file_available || downloading === report.id}
                      className={`flex items-center gap-1.5 text-xs font-semibold transition-colors ${
                        report.file_available
                          ? 'text-[#D1353B] hover:text-[#a82028] cursor-pointer'
                          : 'text-gray-300 cursor-not-allowed'
                      }`}
                    >
                      <FiDownload className="w-3.5 h-3.5" />
                      {downloading === report.id ? 'Downloading…' : 'Download'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
