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
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [loadingTrend, setLoadingTrend] = useState(false);
  const [ticketsError, setTicketsError] = useState<string>("");
  const [trendError, setTrendError] = useState<string>("");

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
