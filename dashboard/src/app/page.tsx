/**
 * INDUSTRIAL ORCHESTRATOR — DASHBOARD OVERVIEW
 * 
 * Main dashboard page with:
 * - Statistics cards showing session/agent/task counts
 * - Active sessions list (Recent activity)
 * - System health indicator
 */

"use client"

import Link from "next/link"
import { useSessionStatistics, useSessions } from "@/lib/api/sessions"
import { useAgentPerformance } from "@/lib/api/agents"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function DashboardPage() {
  // Data Fetching
  const { data: stats, isLoading: isStatsLoading } = useSessionStatistics()
  const { data: agents, isLoading: isAgentsLoading } = useAgentPerformance()
  const { data: recentSessions, isLoading: isSessionsLoading } = useSessions({ pageSize: 5 })

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight mb-2 font-mono">
          SYSTEM OVERVIEW
        </h1>
        <p className="text-muted-foreground text-sm font-mono">
          Real-time orchestration status and session monitoring
        </p>
      </header>

      {/* Statistics Cards */}
      <section className="mb-8">
        <h2 className="text-label mb-4">SESSION METRICS</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="RUNNING"
            value={stats?.by_status.RUNNING ?? 0}
            status="running"
            loading={isStatsLoading}
          />
          <StatCard
            label="PENDING"
            value={stats?.by_status.PENDING ?? 0}
            status="pending"
            loading={isStatsLoading}
          />
          <StatCard
            label="COMPLETED"
            value={stats?.by_status.COMPLETED ?? 0}
            status="completed"
            loading={isStatsLoading}
          />
          <StatCard
            label="FAILED"
            value={stats?.by_status.FAILED ?? 0}
            status="failed"
            loading={isStatsLoading}
          />
        </div>
      </section>

      {/* Agent Status */}
      <section className="mb-8">
        <h2 className="text-label mb-4">AGENT STATUS</h2>
        <div className="grid grid-cols-2 gap-4">
          <Card className="flex flex-col justify-center">
            <div className="text-muted-foreground text-[10px] uppercase tracking-wider mb-1">
              TOTAL AGENTS
            </div>
            {isAgentsLoading ? (
              <div className="h-8 w-16 bg-muted animate-pulse" />
            ) : (
              <div className="text-3xl font-bold tabular-nums font-mono">
                {agents?.total_agents ?? 0}
              </div>
            )}
          </Card>
          <Card className="flex flex-col justify-center">
            <div className="text-muted-foreground text-[10px] uppercase tracking-wider mb-1">
              ACTIVE NOW
            </div>
            {isAgentsLoading ? (
              <div className="h-8 w-16 bg-muted animate-pulse" />
            ) : (
              <div className="text-3xl font-bold tabular-nums font-mono text-status-running">
                {agents?.active_agents ?? 0}
              </div>
            )}
          </Card>
        </div>
      </section>

      {/* Active Sessions Table */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-label">RECENT ACTIVITY</h2>
          <Link href="/sessions" className="text-xs text-accent hover:underline font-mono uppercase">
            View All →
          </Link>
        </div>
        
        <Card className="p-0 overflow-hidden min-h-[200px]">
          {isSessionsLoading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 bg-muted/50 animate-pulse" />
              ))}
            </div>
          ) : recentSessions?.items.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground font-mono text-sm">
              NO RECENT ACTIVITY
            </div>
          ) : (
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
                {recentSessions?.items.map((session) => (
                  <tr
                    key={session.id}
                    className="border-b border-border hover:bg-muted transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="font-medium font-mono">{session.title}</span>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={session.status} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-sm tabular-nums font-mono">
                      {session.started_at ? new Date(session.started_at).toLocaleTimeString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link 
                        href={`/sessions/${session.id}`}
                        className="text-accent hover:underline text-sm font-mono uppercase"
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </section>
    </div>
  )
}

/**
 * Statistics Card Component
 */
function StatCard({
  label,
  value,
  status,
  loading
}: {
  label: string
  value: number
  status: "running" | "pending" | "completed" | "failed"
  loading: boolean
}) {
  const statusColors = {
    running: "text-status-running",
    pending: "text-status-pending",
    completed: "text-status-completed",
    failed: "text-status-failed",
  }

  return (
    <Card className="flex flex-col justify-center">
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 ${status === "running" ? "bg-status-running animate-pulse" : `bg-status-${status}`}`}></span>
        <span className="text-muted-foreground text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      {loading ? (
        <div className="h-8 w-16 bg-muted animate-pulse" />
      ) : (
        <div className={`text-3xl font-bold tabular-nums font-mono ${statusColors[status]}`}>
          {value}
        </div>
      )}
    </Card>
  )
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
  }

  return (
    <Badge className={`border ${statusStyles[status] || "bg-muted text-muted-foreground border-border"}`}>
      {status}
    </Badge>
  )
}