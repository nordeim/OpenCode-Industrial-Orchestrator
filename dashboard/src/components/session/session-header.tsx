"use client"

import { useRouter } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { useSession, useStartSession, useCancelSession } from "@/lib/api/sessions"
import type { Session } from "@/lib/api/types"

interface SessionHeaderProps {
  session: Session
}

export function SessionHeader({ session }: SessionHeaderProps) {
  const router = useRouter()
  const { mutate: startSession, isPending: isStarting } = useStartSession()
  const { mutate: cancelSession, isPending: isCancelling } = useCancelSession()

  const statusVariant = {
    RUNNING: "success",
    COMPLETED: "success",
    FAILED: "error",
    PENDING: "warning",
    PAUSED: "warning",
    CANCELLED: "neutral",
    QUEUED: "neutral",
  }[session.status] as any

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b-2 border-border">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <button 
            onClick={() => router.back()}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            ←
          </button>
          <h1 className="text-2xl font-bold tracking-tight font-mono">
            {session.title}
          </h1>
          <Badge variant={statusVariant}>{session.status}</Badge>
        </div>
        
        <div className="flex gap-6 text-xs text-muted-foreground font-mono">
          <div>
            <span className="opacity-50 mr-2">ID:</span>
            {session.id}
          </div>
          <div>
            <span className="opacity-50 mr-2">TYPE:</span>
            {session.type}
          </div>
          <div>
            <span className="opacity-50 mr-2">CREATED:</span>
            {new Date(session.created_at).toLocaleString()}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {session.status === "PENDING" && (
          <button
            onClick={() => startSession(session.id)}
            disabled={isStarting}
            className="btn-industrial bg-status-running/10 border-status-running text-status-running hover:bg-status-running hover:text-white"
          >
            {isStarting ? "STARTING..." : "▶ START EXECUTION"}
          </button>
        )}

        {session.status === "RUNNING" && (
          <button
            onClick={() => cancelSession({ id: session.id })}
            disabled={isCancelling}
            className="btn-industrial bg-status-failed/10 border-status-failed text-status-failed hover:bg-status-failed hover:text-white"
          >
            {isCancelling ? "STOPPING..." : "■ STOP"}
          </button>
        )}

        {(session.status === "FAILED" || session.status === "CANCELLED") && (
          <button
            onClick={() => startSession(session.id)}
            className="btn-industrial"
          >
            ↻ RETRY
          </button>
        )}
      </div>
    </div>
  )
}
