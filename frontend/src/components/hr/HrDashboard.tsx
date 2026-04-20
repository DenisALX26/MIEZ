import React from 'react';

type HrKpiResponse = {
  total_employees: number;
  new_hires_this_month: number;
  leave_requests_this_month: number;
  pending_leave_requests: number;
  full_time_employees: number;
  non_full_time_employees: number;
  retention_rate: number;
  active_employees: number;
};

const UsersIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const BriefcaseIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

const TrendingUpIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

const HrDashboard = () => {
  const [kpis, setKpis] = React.useState<HrKpiResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    const loadHrKpis = async () => {
      try {
        setLoading(true);
        setError('');

        const response = await fetch('/api/hr/dashboard/', {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`HR KPI request failed: ${response.status}`);
        }

        const data = (await response.json()) as HrKpiResponse;
        setKpis(data);
      } catch (fetchError) {
        console.error('Failed to load HR dashboard KPIs:', fetchError);
        setError('Could not load HR KPI data right now.');
      } finally {
        setLoading(false);
      }
    };

    loadHrKpis();
  }, []);

  const kpiData = [
    { 
      id: 1, 
      title: 'Total Employees', 
      value: String(kpis?.total_employees ?? 0), 
      trend: `+${kpis?.new_hires_this_month ?? 0} this month`, 
      isPositive: true,
      icon: <UsersIcon />, 
      color: 'text-blue-600', 
      bg: 'bg-blue-50' 
    },
    { 
      id: 2, 
      title: 'Leave Requests', 
      value: String(kpis?.leave_requests_this_month ?? 0), 
      trend: `${kpis?.pending_leave_requests ?? 0} pending approval`, 
      isPositive: false,
      icon: <CalendarIcon />, 
      color: 'text-orange-600', 
      bg: 'bg-orange-50' 
    },
    { 
      id: 3, 
      title: 'Full-Time Employees', 
      value: String(kpis?.full_time_employees ?? 0), 
      trend: `${kpis?.non_full_time_employees ?? 0} non-full-time`, 
      isPositive: true,
      icon: <BriefcaseIcon />, 
      color: 'text-purple-600', 
      bg: 'bg-purple-50' 
    },
    { 
      id: 4, 
      title: 'Retention Rate', 
      value: `${(kpis?.retention_rate ?? 0).toFixed(1)}%`, 
      trend: `${kpis?.active_employees ?? 0}/${kpis?.total_employees ?? 0} active`, 
      isPositive: true,
      icon: <TrendingUpIcon />, 
      color: 'text-emerald-600', 
      bg: 'bg-emerald-50' 
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">HR Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Overview of human resources metrics and KPIs.</p>
        {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
      </div>

      {loading && <p className="text-gray-500 text-sm mb-4">Loading KPI data...</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiData.map((kpi) => (
          <div key={kpi.id} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl ${kpi.bg} ${kpi.color}`}>
                {kpi.icon}
              </div>
            </div>
            
            <div>
              <h3 className="text-gray-500 text-sm font-medium">{kpi.title}</h3>
              <p className="text-3xl font-bold text-gray-900 mt-1">{kpi.value}</p>
            </div>
            
            <div className="mt-4">
              <span className={`text-xs font-medium ${kpi.isPositive ? 'text-emerald-600' : 'text-orange-600'}`}>
                {kpi.trend}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HrDashboard;