import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface TicketTrendWeek {
  week_start: string;
  opened_count: number;
  closed_count: number;
}

interface ItTicketTrendChartProps {
  loading: boolean;
  error: string;
  ticketTrend: TicketTrendWeek[];
}

const formatTrendWeekLabel = (weekStart: string): string => {
  const parsed = new Date(weekStart);
  if (Number.isNaN(parsed.getTime())) {
    return "W1";
  }

  const month = parsed.toLocaleDateString(undefined, { month: "short" });
  const weekOfMonth = Math.min(4, Math.ceil(parsed.getDate() / 7));

  return `W${weekOfMonth} ${month}`.trim();
};

const ItTicketTrendChart = ({ loading, error, ticketTrend }: ItTicketTrendChartProps) => {
  const chartData = ticketTrend.map(week => ({
    label: formatTrendWeekLabel(week.week_start),
    Opened: week.opened_count,
    Closed: week.closed_count,
  }))

  return (
    <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5">
      <header className="mb-4">
        <h2 className="text-[1.05rem] font-semibold tracking-tight">Tickets Opened vs Closed</h2>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">Weekly throughput for the last 6 weeks.</p>
      </header>

      {loading ? (
        <p className="text-sm text-[var(--muted-foreground)]">Loading throughput chart...</p>
      ) : error ? (
        <p className="text-sm text-[var(--destructive)]">{error}</p>
      ) : (
        <div className="h-[260px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 4, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid var(--border)' }} />
              <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />
              <Bar dataKey="Opened" fill="var(--primary)" radius={[6, 6, 0, 0]} />
              <Bar dataKey="Closed" fill="#D48A6B" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
};

export default ItTicketTrendChart;
