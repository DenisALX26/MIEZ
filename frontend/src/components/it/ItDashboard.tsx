import type { IconType } from "react-icons";
import StatsCard from "./StatsCard";
import ItTicketTrendChart from "./ItTicketTrendChart";
import ItTicketsSection from "./ItTicketsSection";
import SystemStatusPanel from "../common/SystemStatusPanel";
import { LuTicket } from "react-icons/lu";
import { IoSunnyOutline } from "react-icons/io5";
import { IoMdCheckmarkCircleOutline } from "react-icons/io";
import { MdAccessTime } from "react-icons/md";
import { FiAlertTriangle } from "react-icons/fi";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface ItStatsResponse {
  open_ticket: number;
  in_progress: number;
  resolved_this_week: number;
  ceo_it_summary: {
    avg_resolution_time_hrs: number;
    sla_met_percentage: number;
    critical_open_tickets?: number;
    critical_open?: number;
  };
}

interface TicketTrendWeek {
  week_start: string;
  opened_count: number;
  closed_count: number;
}

interface TechnicianStat {
  user_id: number;
  username: string;
  resolved_count: number;
  avg_resolution_hours: number;
  sla_percent: number;
}

type TechnicianWindow = 7 | 30 | 90;

type TicketStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";
type TicketPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

interface TicketItem {
  id: number;
  ticket_number: string;
  title: string;
  description: string;
  priority: TicketPriority;
  status: TicketStatus;
  department_name: string | null;
  requested_by_username: string | null;
  assigned_to_username: string | null;
  location: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

interface StatConfig {
  title: string;
  icon: IconType;
  iconColor: string;
  getValue: (stats: ItStatsResponse) => number;
  suffix?: string;
}

const ItDashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<ItStatsResponse | null>(null);
  const [tickets, setTickets] = useState<TicketItem[]>([]);
  const [ticketTrend, setTicketTrend] = useState<TicketTrendWeek[]>([]);
  const [technicianStats, setTechnicianStats] = useState<TechnicianStat[]>([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [loadingTrend, setLoadingTrend] = useState(false);
  const [loadingTechnicianStats, setLoadingTechnicianStats] = useState(false);
  const [ticketsError, setTicketsError] = useState<string>("");
  const [trendError, setTrendError] = useState<string>("");
  const [technicianStatsError, setTechnicianStatsError] = useState<string>("");
  const [technicianWindow, setTechnicianWindow] = useState<TechnicianWindow>(30);

  const cardsConfig: StatConfig[] = useMemo(() => {
    if (user?.role === "CEO") {
      return [
        {title: "Open Tickets", icon: LuTicket, iconColor: "open-tickets-icon", getValue: (s) => s.open_ticket},
        {title: "Avg. Resolution Time", icon: MdAccessTime, iconColor: "open-tickets-icon", getValue: (s) => s.ceo_it_summary.avg_resolution_time_hrs, suffix: "hrs"},
        {title: "SLA Compliance", icon: IoMdCheckmarkCircleOutline, iconColor: "chart-2", getValue: (s) => s.ceo_it_summary.sla_met_percentage, suffix: "%"},
        {title: "Critical Open Tickets", icon: FiAlertTriangle, iconColor: "critical-tickets-icon", getValue: (s) => s.ceo_it_summary.critical_open ?? s.ceo_it_summary.critical_open_tickets ?? 0},
      ];
    }

    return [
      {title: "Open Tickets", icon: LuTicket, iconColor: "open-tickets-icon", getValue: (s) => s.open_ticket},
      {title: "In Progress", icon: IoSunnyOutline, iconColor: "open-tickets-icon", getValue: (s) => s.in_progress},
      {title: "Resolved This Week", icon: IoMdCheckmarkCircleOutline, iconColor: "chart-2", getValue: (s) => s.resolved_this_week}
    ];
  }, [user?.role]);

  useEffect(() => {
    fetch("/api/it/dashboard/", { credentials: "include" })
    .then((res) => {
      if (!res.ok) {
        throw new Error(`Stats request failed: ${res.status}`);
      }
      return res.json();
    })
    .then((data: ItStatsResponse) => {
      setStats(data);
      setLoadingStats(false);
    })
    .catch((err) => {
      console.error("Error fetching IT dashboard stats:", err);
      setLoadingStats(false);
    });
  }, []);

  useEffect(() => {
    if (user?.role !== "CEO") {
      setLoadingTrend(false);
      setTicketTrend([]);
      return;
    }

    setLoadingTrend(true);
    fetch("/api/it/ticket-trend/", { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Trend request failed: ${res.status}`);
        }
        return res.json();
      })
      .then((data: { weeks?: TicketTrendWeek[] }) => {
        setTicketTrend(Array.isArray(data.weeks) ? data.weeks : []);
        setLoadingTrend(false);
      })
      .catch((err) => {
        console.error("Error fetching IT ticket trend:", err);
        setTrendError("Could not load ticket trend.");
        setLoadingTrend(false);
      });
  }, [user?.role]);

  useEffect(() => {
    const fetchAllTickets = async () => {
      try {
        setLoadingTickets(true);
        setTicketsError("");

        let nextUrl: string | null = "/api/tickets/?page_size=10";
        const allTickets: TicketItem[] = [];

        while (nextUrl) {
          const response = await fetch(nextUrl, {
            credentials: "include",
          });

          if (!response.ok) {
            throw new Error(`Ticket request failed: ${response.status}`);
          }

          const data = await response.json();
          const pageItems = Array.isArray(data.results) ? (data.results as TicketItem[]) : [];
          allTickets.push(...pageItems);
          nextUrl = typeof data.next === "string" ? new URL(data.next).pathname + new URL(data.next).search : null;
        }

        setTickets(allTickets);
      } catch (err) {
        console.error("Error fetching tickets:", err);
        setTicketsError("Could not load tickets.");
      } finally {
        setLoadingTickets(false);
      }
    };

    fetchAllTickets();
  }, []);

  useEffect(() => {
    if (user?.role !== "IT" && user?.role !== "CEO") {
      setTechnicianStats([]);
      setTechnicianStatsError("");
      setLoadingTechnicianStats(false);
      return;
    }

    const fetchTechnicianStats = async () => {
      try {
        setLoadingTechnicianStats(true);
        setTechnicianStatsError("");

        const response = await fetch(`/api/it/technician-stats/?days=${technicianWindow}`, {
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error(`Technician stats request failed: ${response.status}`);
        }

        const data = await response.json() as { technicians?: TechnicianStat[] };
        setTechnicianStats(Array.isArray(data.technicians) ? data.technicians : []);
      } catch (error) {
        console.error("Error fetching technician stats:", error);
        setTechnicianStatsError("Could not load technician performance stats.");
      } finally {
        setLoadingTechnicianStats(false);
      }
    };

    fetchTechnicianStats();
  }, [technicianWindow, user?.role]);

  const technicianChartData = useMemo(() => {
    return [...technicianStats]
      .sort((a, b) => b.resolved_count - a.resolved_count || a.username.localeCompare(b.username))
      .map((technician) => ({
        name: technician.username,
        resolved: technician.resolved_count,
      }));
  }, [technicianStats]);


  if (loadingStats) return <div className="p-6">Loading data...</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {cardsConfig.map((config, index) => (
          <StatsCard
            key={index}
            title={config.title}
            icon={config.icon}
            iconColor={config.iconColor}
            value={stats ? config.getValue(stats) : 0}
            suffix={config.suffix}
          />
        ))}
      </div>

      <section className="bg-[var(--card)] text-[var(--card-foreground)] border border-[var(--border)] rounded-2xl p-5 space-y-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-[1.05rem] font-semibold tracking-tight">Technician Performance</h2>
            <p className="text-sm text-[var(--muted-foreground)] mt-1">
              Resolved tickets, average resolution time, and SLA compliance for the selected window.
            </p>
          </div>

          <div className="inline-flex rounded-lg border border-[var(--border)] bg-[var(--input-background)] p-1 w-fit">
            {([7, 30, 90] as TechnicianWindow[]).map((days) => (
              <button
                key={days}
                type="button"
                onClick={() => setTechnicianWindow(days)}
                className={`cursor-pointer rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  technicianWindow === days
                    ? "bg-[var(--card)] text-[var(--foreground)] shadow-sm"
                    : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>

        {loadingTechnicianStats ? (
          <p className="text-sm text-[var(--muted-foreground)]">Loading technician stats...</p>
        ) : technicianStatsError ? (
          <p className="text-sm text-[var(--destructive)]">{technicianStatsError}</p>
        ) : technicianStats.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">No resolved tickets were found in the selected window.</p>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="overflow-x-auto border border-[var(--border)] rounded-xl">
              <table className="min-w-full bg-[var(--card)] text-sm">
                <thead className="bg-[var(--input-background)]">
                  <tr>
                    {['Technician', 'Resolved', 'Avg. Resolution', 'SLA %'].map((heading) => (
                      <th
                        key={heading}
                        className="px-4 py-2.5 text-left text-[11px] uppercase tracking-[0.14em] font-semibold text-[var(--muted-foreground)]"
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {technicianStats.map((technician) => (
                    <tr key={technician.user_id} className="border-t border-[var(--border)] hover:bg-[var(--input-background)] transition-colors">
                      <td className="px-4 py-2.5 font-medium">{technician.username}</td>
                      <td className="px-4 py-2.5 whitespace-nowrap">{technician.resolved_count}</td>
                      <td className="px-4 py-2.5 whitespace-nowrap">{technician.avg_resolution_hours.toFixed(2)} hrs</td>
                      <td className="px-4 py-2.5 whitespace-nowrap">{technician.sla_percent.toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="h-[320px] border border-[var(--border)] rounded-xl p-3">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={technicianChartData} margin={{ top: 12, right: 8, left: -10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} interval={0} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ borderRadius: 8, border: "1px solid var(--border)" }}
                    formatter={(value: any) => [value, "Resolved"]}
                  />
                  <Bar dataKey="resolved" fill="var(--primary)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={`${user?.role === "CEO" ? "lg:col-span-2" : "lg:col-span-3"} space-y-6`}>
          {user?.role === "CEO" && (
            <ItTicketTrendChart
              loading={loadingTrend}
              error={trendError}
              ticketTrend={ticketTrend}
            />
          )}

          <ItTicketsSection
            userRole={user?.role}
            currentUserId={user?.id}
            currentUserUsername={user?.username}
            tickets={tickets}
            loadingTickets={loadingTickets}
            ticketsError={ticketsError}
            onTicketUpdated={(updatedTicket) => {
              setTickets((prev) => prev.map((ticket) => (ticket.id === updatedTicket.id ? updatedTicket : ticket)));
            }}
          />
        </div>

        {user?.role === "CEO" && (
          <div className="lg:col-span-1">
            <SystemStatusPanel />
          </div>
        )}
      </div>
    </div>
  );
};

export default ItDashboard;
