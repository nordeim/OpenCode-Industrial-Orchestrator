"use client"

import { use } from "react"
import { useRouter } from "next/navigation"
import { useQueryClient } from "@tanstack/react-query"
import { useSession, sessionKeys } from "@/lib/api/sessions"
import { useSessionEvents } from "@/lib/websocket/provider"
import { SessionHeader } from "@/components/session/session-header"
import { LiveLogs } from "@/components/session/live-logs"
import { SessionMetrics } from "@/components/session/session-metrics"
import { CheckpointTimeline } from "@/components/session/checkpoint-timeline"
import { Card } from "@/components/ui/card"

export default function SessionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const resolvedParams = use(params)
  const sessionId = resolvedParams.id
  const queryClient = useQueryClient()

  // 1. Fetch initial session data
  const { 
    data: session, 
    isLoading, 
    isError,
    error 
  } = useSession(sessionId)

  // 2. Connect to real-time events
  useSessionEvents(sessionId, {
    onStatusChanged: (payload: unknown) => {
      console.log("[Page] Status changed:", payload)
      // Invalidate query to refetch fresh session state
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(sessionId) })
    },
    onMetricsUpdated: () => {
      // Optimistically update metrics if payload contains them
      // Or just invalidate to refetch
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(sessionId) })
    },
    onCheckpointCreated: () => {
      queryClient.invalidateQueries({ queryKey: sessionKeys.detail(sessionId) })
    }
  })

  // 3. Loading State
  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-accent border-t-transparent animate-spin rounded-full"></div>
          <p className="text-muted-foreground font-mono animate-pulse">ESTABLISHING UPLINK...</p>
        </div>
      </div>
    )
  }

  // 4. Error State
  if (isError || !session) {
    return (
      <div className="p-8">
        <Card className="border-status-failed bg-status-failed/5">
          <h1 className="text-xl font-bold text-status-failed mb-2">UPLINK FAILED</h1>
          <p className="text-muted-foreground mb-4">
            Could not retrieve session data. The session ID might be invalid or the orchestrator is offline.
          </p>
          <div className="font-mono text-xs bg-black/20 p-2 mb-4">
            ERROR: {error?.message || "Unknown error"}
          </div>
          <button 
            onClick={() => router.push('/sessions')}
            className="btn-industrial bg-card hover:bg-muted"
          >
            ← RETURN TO LIST
          </button>
        </Card>
      </div>
    )
  }

  // 5. Render "Glass Box" Interface
  return (
    <div className="p-6 h-[calc(100vh-64px)] overflow-y-auto">
      {/* Top Header with Controls */}
      <SessionHeader session={session} />

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100%-120px)] min-h-[500px]">
        
        {/* Left Column: Live Terminal (2/3 width) */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="flex-1 min-h-[400px]">
            <LiveLogs sessionId={sessionId} />
          </div>
          
          {/* Task Hierarchy (Placeholder for now, can be expanded) */}
          <div className="h-[200px]">
             <Card title="ACTIVE TASK CONTEXT" className="h-full">
               <div className="text-muted-foreground text-sm flex items-center justify-center h-full">
                  Waiting for Task Execution...
               </div>
             </Card>
          </div>
        </div>

        {/* Right Column: Telemetry (1/3 width) */}
        <div className="flex flex-col gap-6">
          {/* Metrics */}
          <div className="flex-none">
            <SessionMetrics metrics={session.metrics} />
          </div>

          {/* Timeline */}
          <div className="flex-1 min-h-[300px]">
            {/* 
              Note: We cast session to any here because our frontend 'Session' type 
              might not strictly define checkpoints yet, but the backend sends them.
              This allows progressive enhancement.
            */}
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <CheckpointTimeline checkpoints={(session as any).checkpoints} />
          </div>
        </div>
      </div>
    </div>
  )
}