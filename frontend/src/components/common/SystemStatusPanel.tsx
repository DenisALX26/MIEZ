import React, { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'

interface SystemStatus {
  id: number
  name: string
  uptime_pct: number
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE'
  last_incident_date: string | null
  created_at: string
  updated_at: string
}

interface SystemStatusPanelProps {
  pollInterval?: number // in milliseconds, default 60000
  compact?: boolean
}

const SystemStatusPanel: React.FC<SystemStatusPanelProps> = ({ 
  pollInterval = 60000, 
  compact = false 
}) => {
  const [systems, setSystems] = useState<SystemStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { user } = useAuth()

  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const response = await fetch('/api/it/system-status/', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        })

        if (!response.ok) {
          throw new Error(`Failed to fetch system status: ${response.statusText}`)
        }

        const data: SystemStatus[] = await response.json()
        setSystems(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchSystemStatus()
    const interval = setInterval(fetchSystemStatus, pollInterval)
    return () => clearInterval(interval)
  }, [pollInterval])

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'ONLINE':
        return 'bg-green-500'
      case 'DEGRADED':
        return 'bg-yellow-500'
      case 'OFFLINE':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusBgColor = (status: string): string => {
    switch (status) {
      case 'ONLINE':
        return 'bg-green-50'
      case 'DEGRADED':
        return 'bg-yellow-50'
      case 'OFFLINE':
        return 'bg-red-50'
      default:
        return 'bg-gray-50'
    }
  }

  // Only show if user is CEO or IT
  if (!user || (user.role !== 'CEO' && user.role !== 'IT')) {
    return null
  }

  if (compact) {
    // Compact view - just show indicator dots
    return (
      <div className="flex gap-2">
        {systems.map((system) => (
          <div key={system.id} className="flex items-center gap-1" title={`${system.name}: ${system.status} (${system.uptime_pct}%)`}>
            <div className={`w-3 h-3 rounded-full ${getStatusColor(system.status)}`} />
            {!compact && <span className="text-xs text-gray-600">{system.name}</span>}
          </div>
        ))}
      </div>
    )
  }

  // Full view
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">System Status</h2>
      
      {loading && <p className="text-gray-500">Loading system status...</p>}
      {error && <p className="text-red-600">Error: {error}</p>}
      
      {!loading && systems.length > 0 && (
        <div className="space-y-3">
          {systems.map((system) => (
            <div key={system.id} className={`rounded-lg p-4 ${getStatusBgColor(system.status)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full ${getStatusColor(system.status)}`} />
                  <div>
                    <h3 className="font-medium text-gray-800">{system.name}</h3>
                    <p className="text-sm text-gray-600">{system.status}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-800">{system.uptime_pct}%</p>
                  <p className="text-xs text-gray-500">uptime</p>
                </div>
              </div>
              {system.last_incident_date && (
                <p className="text-xs text-gray-600 mt-2">
                  Last incident: {new Date(system.last_incident_date).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && systems.length === 0 && (
        <p className="text-gray-500">No systems found</p>
      )}
    </div>
  )
}

export default SystemStatusPanel
