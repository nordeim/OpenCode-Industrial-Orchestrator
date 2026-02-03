/**
 * SESSIONS LIST PAGE
 * 
 * Displays all sessions with filtering and search capabilities.
 */

import Link from "next/link";

// Mock data
const MOCK_SESSIONS = [
    { id: "1", title: "Session-Alpha-001", status: "RUNNING", type: "CODING", priority: "HIGH", createdAt: "2026-02-03T10:00:00Z" },
    { id: "2", title: "Session-Beta-002", status: "RUNNING", type: "DEBUGGING", priority: "MEDIUM", createdAt: "2026-02-03T09:45:00Z" },
    { id: "3", title: "Session-Gamma-003", status: "PENDING", type: "REFACTORING", priority: "LOW", createdAt: "2026-02-03T09:30:00Z" },
    { id: "4", title: "Session-Delta-004", status: "COMPLETED", type: "CODING", priority: "HIGH", createdAt: "2026-02-03T08:00:00Z" },
    { id: "5", title: "Session-Epsilon-005", status: "FAILED", type: "DEBUGGING", priority: "CRITICAL", createdAt: "2026-02-03T07:30:00Z" },
    { id: "6", title: "Session-Zeta-006", status: "PAUSED", type: "CODING", priority: "MEDIUM", createdAt: "2026-02-03T06:00:00Z" },
];

const STATUS_FILTERS = ["ALL", "RUNNING", "PENDING", "COMPLETED", "FAILED", "PAUSED"];

export default function SessionsPage() {
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
                            className={`
                px-3 py-1.5 text-xs font-semibold uppercase tracking-wider
                border-2 transition-all
                ${filter === "ALL"
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
                            {MOCK_SESSIONS.map((session) => (
                                <tr
                                    key={session.id}
                                    className="border-b border-border hover:bg-muted transition-colors"
                                >
                                    <td className="px-4 py-3">
                                        <Link
                                            href={`/sessions/${session.id}`}
                                            className="font-medium hover:text-accent transition-colors"
                                        >
                                            {session.title}
                                        </Link>
                                    </td>
                                    <td className="px-4 py-3">
                                        <StatusBadge status={session.status} />
                                    </td>
                                    <td className="px-4 py-3 text-sm text-muted-foreground">
                                        {session.type}
                                    </td>
                                    <td className="px-4 py-3">
                                        <PriorityBadge priority={session.priority} />
                                    </td>
                                    <td className="px-4 py-3 text-muted-foreground text-sm tabular-nums">
                                        {new Date(session.createdAt).toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex gap-2 justify-end">
                                            <button className="text-accent hover:underline text-sm">
                                                View
                                            </button>
                                            <button className="text-muted-foreground hover:text-foreground text-sm">
                                                Stop
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* Pagination */}
            <section className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
                <div>
                    Showing 1-6 of 6 sessions
                </div>
                <div className="flex gap-2">
                    <button className="px-3 py-1 border-2 border-border hover:border-accent disabled:opacity-50" disabled>
                        ← Prev
                    </button>
                    <button className="px-3 py-1 border-2 border-border hover:border-accent disabled:opacity-50" disabled>
                        Next →
                    </button>
                </div>
            </section>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const statusStyles: Record<string, string> = {
        RUNNING: "bg-status-running/20 text-status-running border-status-running",
        PENDING: "bg-status-pending/20 text-status-pending border-status-pending",
        COMPLETED: "bg-status-completed/20 text-status-completed border-status-completed",
        FAILED: "bg-status-failed/20 text-status-failed border-status-failed",
        PAUSED: "bg-status-paused/20 text-status-paused border-status-paused",
    };

    return (
        <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold border uppercase tracking-wider ${statusStyles[status] || "bg-muted text-muted-foreground border-border"}`}>
            {status}
        </span>
    );
}

function PriorityBadge({ priority }: { priority: string }) {
    const priorityStyles: Record<string, string> = {
        CRITICAL: "text-status-failed",
        HIGH: "text-status-pending",
        MEDIUM: "text-foreground",
        LOW: "text-muted-foreground",
    };

    return (
        <span className={`text-xs font-semibold uppercase ${priorityStyles[priority] || "text-muted-foreground"}`}>
            {priority}
        </span>
    );
}
