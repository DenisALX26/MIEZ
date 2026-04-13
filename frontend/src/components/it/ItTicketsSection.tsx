import { useEffect, useMemo, useState } from "react";

type TicketStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";
type TicketPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

type SortKey =
  | "ticket_number"
  | "title"
  | "priority"
  | "status"
  | "department_name"
  | "requested_by_username"
  | "assigned_to_username"
  | "location"
  | "created_at"
  | "updated_at"
  | "resolved_at";

type SortDirection = "asc" | "desc";

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

interface ItTicketsSectionProps {
  userRole?: string;
  tickets: TicketItem[];
  loadingTickets: boolean;
  ticketsError: string;
}

const statusBadgeClass: Record<TicketStatus, string> = {
  OPEN: "bg-blue-50 text-blue-800 border border-blue-200",
  IN_PROGRESS: "bg-amber-50 text-amber-800 border border-amber-200",
  RESOLVED: "bg-emerald-50 text-emerald-800 border border-emerald-200",
  CLOSED: "bg-slate-100 text-slate-700 border border-slate-300",
};

const priorityBadgeClass: Record<TicketPriority, string> = {
  LOW: "bg-slate-100 text-slate-700 border border-slate-200",
  MEDIUM: "bg-blue-50 text-blue-700 border border-blue-200",
  HIGH: "bg-orange-50 text-orange-700 border border-orange-200",
  URGENT: "bg-red-50 text-red-700 border border-red-200",
};

const priorityDotClass: Record<TicketPriority, string> = {
  LOW: "bg-[var(--low-priority-tickets-icon)]",
  MEDIUM: "bg-[var(--normal-priority-tickets-icon)]",
  HIGH: "bg-[var(--high-priority-tickets-icon)]",
  URGENT: "bg-[var(--urgent-priority-tickets-icon)]",
};

const formatDateTime = (value: string | null): string => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleString();
};

const formatDateOnly = (value: string | null): string => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";

  const day = String(parsed.getDate()).padStart(2, "0");
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const year = parsed.getFullYear();
  return `${day}/${month}/${year}`;
};

const normalizeValue = (value: string | null | undefined): string => (value ?? "").toLowerCase();

const ItTicketsSection = ({ userRole, tickets, loadingTickets, ticketsError }: ItTicketsSectionProps) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | TicketStatus>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<"ALL" | TicketPriority>("ALL");
  const [departmentFilter, setDepartmentFilter] = useState("ALL");
  const [assigneeFilter, setAssigneeFilter] = useState("ALL");
  const [requesterFilter, setRequesterFilter] = useState("ALL");
  const [isFilterModalOpen, setIsFilterModalOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<TicketItem | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") {
        return;
      }

      if (selectedTicket) {
        setSelectedTicket(null);
        return;
      }

      if (isFilterModalOpen) {
        setIsFilterModalOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isFilterModalOpen, selectedTicket]);

  const roleScopedTickets = useMemo(() => {
    const ceoRestricted = userRole === "CEO";
    return tickets.filter((ticket) => {
      if (ceoRestricted && !(ticket.priority === "HIGH" || ticket.priority === "URGENT")) {
        return false;
      }
      return true;
    });
  }, [tickets, userRole]);

  const visibleTickets = useMemo(() => {
    return roleScopedTickets.filter((ticket) => {
      if (statusFilter !== "ALL" && ticket.status !== statusFilter) {
        return false;
      }

      if (priorityFilter !== "ALL" && ticket.priority !== priorityFilter) {
        return false;
      }

      if (departmentFilter !== "ALL" && (ticket.department_name ?? "Unassigned") !== departmentFilter) {
        return false;
      }

      if (assigneeFilter !== "ALL" && (ticket.assigned_to_username ?? "Unassigned") !== assigneeFilter) {
        return false;
      }

      if (requesterFilter !== "ALL" && (ticket.requested_by_username ?? "Unknown") !== requesterFilter) {
        return false;
      }

      if (!searchTerm.trim()) {
        return true;
      }

      const query = searchTerm.trim().toLowerCase();
      return (
        normalizeValue(ticket.ticket_number).includes(query) ||
        normalizeValue(ticket.title).includes(query) ||
        normalizeValue(ticket.description).includes(query) ||
        normalizeValue(ticket.department_name).includes(query) ||
        normalizeValue(ticket.requested_by_username).includes(query) ||
        normalizeValue(ticket.assigned_to_username).includes(query) ||
        normalizeValue(ticket.location).includes(query)
      );
    });
  }, [
    roleScopedTickets,
    statusFilter,
    priorityFilter,
    departmentFilter,
    assigneeFilter,
    requesterFilter,
    searchTerm,
  ]);

  const sortedTickets = useMemo(() => {
    const priorityOrder: Record<TicketPriority, number> = { LOW: 1, MEDIUM: 2, HIGH: 3, URGENT: 4 };
    const statusOrder: Record<TicketStatus, number> = { OPEN: 1, IN_PROGRESS: 2, RESOLVED: 3, CLOSED: 4 };

    const sorted = [...visibleTickets].sort((a, b) => {
      let left: string | number = "";
      let right: string | number = "";

      if (sortKey === "priority") {
        left = priorityOrder[a.priority];
        right = priorityOrder[b.priority];
      } else if (sortKey === "status") {
        left = statusOrder[a.status];
        right = statusOrder[b.status];
      } else if (sortKey === "created_at" || sortKey === "updated_at" || sortKey === "resolved_at") {
        left = a[sortKey] ? new Date(a[sortKey] as string).getTime() : 0;
        right = b[sortKey] ? new Date(b[sortKey] as string).getTime() : 0;
      } else {
        left = normalizeValue(a[sortKey] as string | null);
        right = normalizeValue(b[sortKey] as string | null);
      }

      if (left < right) {
        return sortDirection === "asc" ? -1 : 1;
      }
      if (left > right) {
        return sortDirection === "asc" ? 1 : -1;
      }
      return 0;
    });

    return sorted;
  }, [visibleTickets, sortKey, sortDirection]);

  const departmentOptions = useMemo(() => {
    const values = new Set(roleScopedTickets.map((t) => t.department_name ?? "Unassigned"));
    return ["ALL", ...Array.from(values).sort((a, b) => a.localeCompare(b))];
  }, [roleScopedTickets]);

  const assigneeOptions = useMemo(() => {
    const values = new Set(roleScopedTickets.map((t) => t.assigned_to_username ?? "Unassigned"));
    return ["ALL", ...Array.from(values).sort((a, b) => a.localeCompare(b))];
  }, [roleScopedTickets]);

  const requesterOptions = useMemo(() => {
    const values = new Set(roleScopedTickets.map((t) => t.requested_by_username ?? "Unknown"));
    return ["ALL", ...Array.from(values).sort((a, b) => a.localeCompare(b))];
  }, [roleScopedTickets]);

  const resetFilters = () => {
    setSearchTerm("");
    setStatusFilter("ALL");
    setPriorityFilter("ALL");
    setDepartmentFilter("ALL");
    setAssigneeFilter("ALL");
    setRequesterFilter("ALL");
  };

  return (
    <section className="bg-white border border-gray-200 rounded-lg p-4 md:p-5 shadow-sm">
      <div className="flex flex-col gap-2 mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Tickets</h2>
        <p className="text-sm text-gray-500">
          {userRole === "CEO"
            ? "CEO view: only HIGH and URGENT priority tickets are shown."
            : "IT view: all tickets are shown."}
        </p>
      </div>

      <div className="flex flex-col md:flex-row md:items-center gap-3 mb-4">
        <button
          type="button"
          onClick={() => setIsFilterModalOpen(true)}
          className="cursor-pointer border border-gray-300 bg-white rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Open Filters
        </button>

        <button
          type="button"
          onClick={resetFilters}
          className="cursor-pointer border border-gray-300 bg-white rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Clear Filters
        </button>

        <select
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
        >
          <option value="ticket_number">Sort by Ticket Number</option>
          <option value="title">Sort by Title</option>
          <option value="priority">Sort by Priority</option>
          <option value="status">Sort by Status</option>
          <option value="department_name">Sort by Department</option>
          <option value="requested_by_username">Sort by Requested By</option>
          <option value="assigned_to_username">Sort by Assigned To</option>
          <option value="location">Sort by Location</option>
          <option value="created_at">Sort by Created At</option>
          <option value="updated_at">Sort by Updated At</option>
          <option value="resolved_at">Sort by Resolved At</option>
        </select>

        <select
          value={sortDirection}
          onChange={(e) => setSortDirection(e.target.value as SortDirection)}
          className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>

        <div className="text-sm text-gray-500">
          {searchTerm.trim() ? `Search: "${searchTerm}"` : "No search query"}
        </div>
      </div>

      <div className="mb-3 text-sm text-gray-600">
        Showing {sortedTickets.length} tickets
      </div>

      {isFilterModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setIsFilterModalOpen(false);
            }
          }}
        >
          <div className="w-full max-w-3xl bg-white border border-gray-200 rounded-lg shadow-lg">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
              <h3 className="text-base font-semibold text-gray-900">Filter Tickets</h3>
              <button
                type="button"
                onClick={() => setIsFilterModalOpen(false)}
                className="cursor-pointer rounded-md px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              >
                Close
              </button>
            </div>

            <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-gray-500 mb-1">Search</label>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search ticket no, title, description, users, location"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as "ALL" | TicketStatus)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="OPEN">NEW</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="RESOLVED">RESOLVED</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Priority</label>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value as "ALL" | TicketPriority)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
                >
                  <option value="ALL">All Priorities</option>
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="URGENT">URGENT</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Department</label>
                <select
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
                >
                  {departmentOptions.map((option) => (
                    <option key={option} value={option}>
                      {option === "ALL" ? "All Departments" : option}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Assignee</label>
                <select
                  value={assigneeFilter}
                  onChange={(e) => setAssigneeFilter(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
                >
                  {assigneeOptions.map((option) => (
                    <option key={option} value={option}>
                      {option === "ALL" ? "All Assignees" : option}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Requester</label>
                <select
                  value={requesterFilter}
                  onChange={(e) => setRequesterFilter(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
                >
                  {requesterOptions.map((option) => (
                    <option key={option} value={option}>
                      {option === "ALL" ? "All Requesters" : option}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-gray-200">
              <button
                type="button"
                onClick={resetFilters}
                className="cursor-pointer border border-gray-300 bg-white rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Reset
              </button>
              <button
                type="button"
                onClick={() => setIsFilterModalOpen(false)}
                className="cursor-pointer border border-gray-800 bg-gray-900 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-gray-800"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}

      {ticketsError ? (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md p-3">{ticketsError}</div>
      ) : loadingTickets ? (
        <div className="text-sm text-gray-500">Loading tickets...</div>
      ) : (
        <div className="overflow-x-auto border border-gray-200 rounded-md">
          <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-gray-500">Ticket Number</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-500">Title</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-500">Requested By</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-500">Priority</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-500">Status</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-500">Created</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedTickets.map((ticket) => (
                <tr key={ticket.id} className="hover:bg-gray-50">
                  <td className="px-3 py-2 font-medium text-gray-500 whitespace-nowrap">{ticket.ticket_number}</td>
                  <td className="px-3 py-2 text-gray-800 min-w-55 font-medium">{ticket.title}</td>
                  <td className="px-3 py-2 text-gray-700 whitespace-nowrap">{ticket.requested_by_username ?? "Unknown"}</td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="inline-flex items-center gap-2 text-sm font-medium text-gray-800">
                      <span className={`h-1.5 w-1.5 rounded-full ${priorityDotClass[ticket.priority]}`} />
                      <span className="capitalize">{ticket.priority.toLowerCase()}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold capitalize ${statusBadgeClass[ticket.status]}`}>
                      {ticket.status.toLowerCase()}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-gray-700 whitespace-nowrap">{formatDateOnly(ticket.created_at)}</td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => setSelectedTicket(ticket)}
                      className="cursor-pointer border border-gray-300 bg-white rounded-md px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {sortedTickets.length === 0 && (
            <div className="p-4 text-sm text-gray-500">No tickets match the current filters.</div>
          )}
        </div>
      )}

      {selectedTicket && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              setSelectedTicket(null);
            }
          }}
        >
          <div className="w-full max-w-2xl bg-white border border-gray-200 rounded-lg shadow-lg">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
              <h3 className="text-base font-semibold text-gray-900">
                Ticket Details: {selectedTicket.ticket_number}
              </h3>
              <button
                type="button"
                onClick={() => setSelectedTicket(null)}
                className="cursor-pointer rounded-md px-2 py-1 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              >
                Close
              </button>
            </div>

            <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Title</div>
                <div className="text-gray-900">{selectedTicket.title}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Department</div>
                <div className="text-gray-900">{selectedTicket.department_name ?? "Unassigned"}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Requested By</div>
                <div className="text-gray-900">{selectedTicket.requested_by_username ?? "Unknown"}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Assigned To</div>
                <div className="text-gray-900">{selectedTicket.assigned_to_username ?? "Unassigned"}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Priority</div>
                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${priorityBadgeClass[selectedTicket.priority]}`}>
                  {selectedTicket.priority}
                </span>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Status</div>
                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${statusBadgeClass[selectedTicket.status]}`}>
                  {selectedTicket.status}
                </span>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Location</div>
                <div className="text-gray-900">{selectedTicket.location || "-"}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Created At</div>
                <div className="text-gray-900">{formatDateTime(selectedTicket.created_at)}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Updated At</div>
                <div className="text-gray-900">{formatDateTime(selectedTicket.updated_at)}</div>
              </div>

              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Resolved At</div>
                <div className="text-gray-900">{formatDateTime(selectedTicket.resolved_at)}</div>
              </div>

              <div className="md:col-span-2">
                <div className="text-xs font-semibold text-gray-500 mb-1">Description</div>
                <div className="text-gray-900 whitespace-pre-wrap">{selectedTicket.description || "-"}</div>
              </div>
            </div>

            <div className="flex justify-end px-5 py-4 border-t border-gray-200">
              <button
                type="button"
                onClick={() => setSelectedTicket(null)}
                className="cursor-pointer border border-gray-800 bg-gray-900 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default ItTicketsSection;
