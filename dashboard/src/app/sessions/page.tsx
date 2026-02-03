/**
 * SESSIONS LIST PAGE
 * 
 * Displays all sessions with filtering and search capabilities.
 * Connected to Industrial Orchestrator API.
 */

"use client"

import { useState } from "react"
import Link from "next/link"
import { useSessions } from "@/lib/api/sessions"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import type { SessionStatus } from "@/lib/api/types"

const STATUS_FILTERS: (SessionStatus | "ALL")[] = [
  "ALL", 
  "RUNNING", 
  "PENDING", 
  "COMPLETED", 
  "FAILED", 
  "PAUSED"
]

export default function SessionsPage() {
  // State
  const [statusFilter, setStatusFilter] = useState<SessionStatus | undefined>(undefined)
  const [page,QP] = useState(1)
  const pageSize = 10

  // Data Fetching
  const { 
    data, 
    isLoading, 
    isError, 
    error 
  } = useSessions({
    status: statusFilter,
    page,
    pageSize
  })

  // Handlers
  const handleFilterChange = (filter: SessionStatus | "ALL") => {
    setStatusFilter(filter === "ALL" ? undefined : filter)
    QP(1) // Reset to page 1 on filter change
  }

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight mb-2">SESSIONS</h1>
          <p className="text-muted-foreground text-sm">
            Manage and monitor coding orchestration sessions
          </p>
        </div>
        <button className="btn-industrial">
          + NEW SESSION
        </button>
      </header>

      {/* Filters */}
      <section className="mb-6">
        <div className="flex gap-2 flex-wrap">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter}
              onClick={() => handleFilterChange(filter)}
              className={`
                px-3 py-1.5 text-xs font-semibold uppercase tracking-wider
                border-2 transition-all
                ${(filter === "ALL" && !statusFilter) || filter === statusFilter
                  ? "bg-accent text-accent-foreground border-accent"
                  : "bg-transparent text-muted-foreground border-border hover:border-accent hover:text-foreground"
                }
              `}
            >
              {filter}
            </button>
          ))}
        </div>
      </section>

      {/* Sessions Table */}
      <section>
        <Card className="p-0 overflow-hidden min-h-[400px]">
          {isLoading ? (
            <div className="p-8 space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-12 bg-muted/50 animate-pulse" />
              ))}
            </div>
          ) : isError ? (
             <div className="p-12 text-center">
               <div className="text-status-failed font-bold mb-2">FAILED TO LOAD SESSIONS</div>
               <div className="text-muted-foreground text-sm font-mono">
                 {error instanceof Error ? error.message : "Unknown connection error"}
               </div>
             </div>
          ) : data?.items.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              NO SESSIONS FOUND
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
                    Type
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider">
                    Priority
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider">
                    Created
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((session) => (
                  <tr
                    key={session.id}
                    className="border-b border-border hover:bg-muted transition-colors group"
                  >
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <Link
                          href={`/sessions/${session.id}`}
                          className="font-medium font-mono hover:text-accent transition-colors"
                        >
                          {session.title}
                        </Link>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          {session.id.split('-')[0]}...
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={session.status} />
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground font-mono">
                      {session.type}
                    </td>
                    <td className="px-4 py-3">
                      <PriorityBadge priority={session.priority} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-sm tabular-nums font-mono">
                      {new Date(session.created_at).toLocaleString()}
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

      {/* Pagination */}
      {data && (
        <section className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
          <div className="font-mono">
            Showing {((page - 1) * pageSize) + 1}-{Math.min(page * pageSize, data.total)} of {data.total}
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => QP(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border-2 border-border hover:border-accent disabled:opacity-50 disabled:hover:border-border font-mono uppercase"
            >
              ← Prev
            </button>
            <button 
              onClick={() => QP(p => p + 1)}
              disabled={!data.has_more}
              className="px-3 py-1 border-2 border-border hover:border-accent disabled:opacity-50 disabled:hover:border-border font-mono uppercase"
            >
              Next →
            </button>
          </div>
        </section>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const statusStyles: Record<string, string> = {
    RUNNING: "bg-status-running/20 text-status-running border-status-running",
    PENDING: "bg-status-pending/20 text-status-pending border-status-pending",
    COMPLETED: "bg-status-completed/20 text-status-completed border-status-completed",
    FAILED: "bg-status-failed/20 text-status-failed border-status-failed",
    PAUSED: "bg-status-paused/20 text-status-paused border-status-paused",
    CANCELLED: "bg-transparent text-muted-foreground border-border",
    QUEUED: "bg-transparent text-muted-foreground border-border"
  };

  return (
    <Badge 
      className={`border ${statusStyles[status] || "bg-muted text-muted-foreground border-border"}`}
    >
      {status}
    </Badge>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const priorityStyles: Record<string, string> = {
    CRITICAL: "text-status-failed font-bold",
    HIGH: "text-status-pending font-bold",
    MEDIUM: "text-foreground",
    LOW: "text-muted-foreground",
  };

  return (
    <span className={`text-xs font-mono uppercase ${priorityStyles[priority] || "text-muted-foreground"}`}>
      {priority}
    </span>
  );
}