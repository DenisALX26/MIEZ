import type { IconType } from "react-icons";
import StatsCard from "./StatsCard";
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
    critical_open_tickets: number;
  };
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
  const [loading, setLoading] = useState(true);

  const cardsConfig: StatConfig[] = useMemo(() => {
    if (user?.role === "CEO") {
      return [
        {title: "Open Tickets", icon: LuTicket, iconColor: "open-tickets-icon", getValue: (s) => s.open_ticket},
        {title: "Avg. Resolution Time", icon: MdAccessTime, iconColor: "open-tickets-icon", getValue: (s) => s.ceo_it_summary.avg_resolution_time_hrs, suffix: "hrs"},
        {title: "SLA Compliance", icon: IoMdCheckmarkCircleOutline, iconColor: "chart-2", getValue: (s) => s.ceo_it_summary.sla_met_percentage, suffix: "%"},
        {title: "Critical Open Tickets", icon: FiAlertTriangle, iconColor: "critical-tickets-icon", getValue: (s) => s.ceo_it_summary.critical_open_tickets},
      ];
    }

    return [
      {title: "Open Tickets", icon: LuTicket, iconColor: "open-tickets-icon", getValue: (s) => s.open_ticket},
      {title: "In Progress", icon: IoSunnyOutline, iconColor: "open-tickets-icon", getValue: (s) => s.in_progress},
      {title: "Resolved This Week", icon: IoMdCheckmarkCircleOutline, iconColor: "chart-2", getValue: (s) => s.resolved_this_week}
    ];
  }, [user?.role]);

  useEffect(() => {
    fetch("http://localhost:8000/api/it/dashboard")
    .then((res) => res.json())
    .then((data: ItStatsResponse) => {
      setStats(data);
      setLoading(false);
    })
    .catch((err) => {
      console.error("Error fetching IT dashboard stats:", err);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-6">Loading data...</div>;

  return (
    <div className="flex flex-col md:flex-row md:w-full w-3/4 items-stretch justify-between gap-4 lg:w-[90%] mx-auto">
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
  );
};

export default ItDashboard;
