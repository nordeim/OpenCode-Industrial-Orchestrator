/**
 * INDUSTRIAL ORCHESTRATOR — DASHBOARD OVERVIEW
 * 
 * Main dashboard page with:
 * - Statistics cards showing session/agent/task counts
 * - Active sessions list
 * - System health indicator
 */

// Mock data for initial development
const MOCK_STATS = {
  running: 12,
  pending: 8,
  completed: 156,
  failed: 3,
  totalAgents: 5,
  activeAgents: 4,
};

const MOCK_SESSIONS = [
  { id: "1", title: "Session-Alpha-001", status: "RUNNING", startedAt: "5m ago" },
  { id: "2", title: "Session-Beta-002", status: "RUNNING", startedAt: "12m ago" },
  { id: "3", title: "Session-Gamma-003", status: "PENDING", startedAt: "—" },
  { id: "4", title: "Session-Delta-004", status: "COMPLETED", startedAt: "1h ago" },
];

export default function DashboardPage() {
  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight mb-2">
          SYSTEM OVERVIEW
        </h1>
        <p className="text-muted-foreground text-sm">
          Real-time orchestration status and session monitoring
        </p>
      </header>

      {/* Statistics Cards */}
      <section className="mb-8">
        <h2 className="text-label mb-4">SESSION METRICS</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="RUNNING"
            value={MOCK_STATS.running}
            status="running"
          />
          <StatCard
            label="PENDING"
            value={MOCK_STATS.pending}
            status="pending"
          />
          <StatCard
            label="COMPLETED"
            value={MOCK_STATS.completed}
            status="completed"
          />
          <StatCard
            label="FAILED"
            value={MOCK_STATS.failed}
            status="failed"
          />
        </div>
      </section>

      {/* Agent Status */}
      <section className="mb-8">
        <h2 className="text-label mb-4">AGENT STATUS</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="industrial-card">
            <div className="text-muted-foreground text-xs mb-1">TOTAL AGENTS</div>
            <div className="text-3xl font-bold tabular-nums">{MOCK_STATS.totalAgents}</div>
          </div>
          <div className="industrial-card">
            <div className="text-muted-foreground text-xs mb-1">ACTIVE NOW</div>
            <div className="text-3xl font-bold tabular-nums text-status-running">
              {MOCK_STATS.activeAgents}
            </div>
          </div>
        </div>
      </section>

      {/* Active Sessions Table */}
      <section>
        <h2 className="text-label mb-4">ACTIVE SESSIONS</h2>
        <div className="industrial-card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-border bg-muted">
                <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider">
                  Session
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider">
                  Started
                </th>
                <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {MOCK_SESSIONS.map((session) => (
                <tr
                  key={session.id}
                  className="border-b border-border hover:bg-muted transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-medium">{session.title}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={session.status} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-sm tabular-nums">
                    {session.startedAt}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-accent hover:underline text-sm">
                      View →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

/**
 * Statistics Card Component
 */
function StatCard({
  label,
  value,
  status
}: {
  label: string;
  value: number;
  status: "running" | "pending" | "completed" | "failed";
}) {
  const statusColors = {
    running: "text-status-running",
    pending: "text-status-pending",
    completed: "text-status-completed",
    failed: "text-status-failed",
  };

  return (
    <div className="industrial-card">
      <div className="flex items-center gap-2 mb-2">
        <span className={`status-dot ${status === "running" ? "status-running" : `bg-status-${status}`}`}></span>
        <span className="text-muted-foreground text-xs">{label}</span>
      </div>
      <div className={`text-3xl font-bold tabular-nums ${statusColors[status]}`}>
        {value}
      </div>
    </div>
  );
}

/**
 * Status Badge Component
 */
function StatusBadge({ status }: { status: string }) {
  const statusStyles: Record<string, string> = {
    RUNNING: "bg-status-running/20 text-status-running border-status-running",
    PENDING: "bg-status-pending/20 text-status-pending border-status-pending",
    COMPLETED: "bg-status-completed/20 text-status-completed border-status-completed",
    FAILED: "bg-status-failed/20 text-status-failed border-status-failed",
    PAUSED: "bg-status-paused/20 text-status-paused border-status-paused",
  };

  return (
    <span
      className={`
        inline-flex items-center px-2 py-1 text-xs font-semibold 
        border uppercase tracking-wider
        ${statusStyles[status] || "bg-muted text-muted-foreground border-border"}
      `}
    >
      {status}
    </span>
  );
}
