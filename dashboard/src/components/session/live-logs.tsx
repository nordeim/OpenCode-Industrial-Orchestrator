"use client"

import { useEffect, useRef, useState } from "react"
import { Card } from "@/components/ui/card"
import { useWebSocket } from "@/lib/websocket/provider"
import { Badge } from "@/components/ui/badge"

interface LogEntry {
  id: string
  level: "INFO" | "WARN" | "ERROR" | "DEBUG"
  message: string
  timestamp: string
}

interface LiveLogsProps {
  sessionId: string
}

export function LiveLogs({ sessionId }: LiveLogsProps) {
  const { subscribe } = useWebSocket()
  const [logs, setLogs] = useState<LogEntry[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  // Subscribe to log events
  useEffect(() => {
    if (!sessionId) return

    const handleLog = (payload: any) => {
      // Validate payload structure (defensive programming)
      if (!payload || typeof payload !== 'object') return

      const newLog: LogEntry = {
        id: crypto.randomUUID(),
        level: payload.level || "INFO",
        message: payload.message || JSON.stringify(payload),
        timestamp: payload.timestamp || new Date().toISOString()
      }

      setLogs(prev => [...prev.slice(-99), newLog]) // Keep last 100 logs
    }

    // Subscribe to session-specific log channel
    // Assumes backend broadcasts "session.log" for the specific room
    const unsubscribe = subscribe("session.log", handleLog)
    
    return () => {
      unsubscribe()
    }
  }, [sessionId, subscribe])

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [logs])

  return (
    <Card title="LIVE LOGS" className="h-[400px] flex flex-col">
      <div className="flex-1 overflow-y-auto font-mono text-xs p-2 space-y-1 bg-black/20 border border-border/50">
        {logs.length === 0 && (
          <div className="text-muted-foreground italic p-2">
            Waiting for logs...
          </div>
        )}
        
        {logs.map((log) => (
          <div key={log.id} className="flex gap-2 items-start hover:bg-muted/50 p-0.5 rounded">
            <span className="text-muted-foreground shrink-0 tabular-nums opacity-50">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <span className={`
              shrink-0 font-bold w-12
              ${log.level === 'ERROR' ? 'text-status-failed' : 
                log.level === 'WARN' ? 'text-status-pending' : 
                'text-status-completed'}
            `}>
              [{log.level}]
            </span>
            <span className="break-all whitespace-pre-wrap text-foreground/90">
              {log.message}
            </span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      
      <div className="mt-2 flex justify-between items-center text-[10px] text-muted-foreground uppercase tracking-wider">
        <div className="flex items-center gap-2">
          <span className="status-dot status-running"></span>
          <span>Live Stream Active</span>
        </div>
        <span>{logs.length} events</span>
      </div>
    </Card>
  )
}
