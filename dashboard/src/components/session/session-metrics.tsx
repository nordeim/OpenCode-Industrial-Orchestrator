import { Card } from "@/components/ui/card"
import type { ExecutionMetrics } from "@/lib/api/types"

interface SessionMetricsProps {
  metrics?: ExecutionMetrics
}

export function SessionMetrics({ metrics }: SessionMetricsProps) {
  if (!metrics) {
    return (
      <Card title="METRICS" className="h-full min-h-[120px] flex items-center justify-center">
        <span className="text-muted-foreground text-xs">NO METRICS AVAILABLE</span>
      </Card>
    )
  }

  const successRate = metrics.total_tasks > 0 
    ? Math.round((metrics.completed_tasks / metrics.total_tasks) * 100) 
    : 0

  const duration = metrics.execution_time_ms 
    ? (metrics.execution_time_ms / 1000).toFixed(1) + "s"
    : "0s"

  return (
    <Card title="EXECUTION METRICS" className="h-full">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-muted-foreground text-[10px] uppercase tracking-wider mb-1">
            Tasks Completed
          </div>
          <div className="text-2xl font-mono font-bold tabular-nums leading-none">
            {metrics.completed_tasks}
            <span className="text-muted-foreground text-sm ml-1">/ {metrics.total_tasks}</span>
          </div>
        </div>

        <div>
          <div className="text-muted-foreground text-[10px] uppercase tracking-wider mb-1">
            Success Rate
          </div>
          <div className={`text-2xl font-mono font-bold tabular-nums leading-none ${
            successRate > 90 ? "text-status-running" : 
            successRate > 70 ? "text-status-pending" : "text-status-failed"
          }`}>
            {successRate}%
          </div>
        </div>

        <div>
          <div className="text-muted-foreground text-[10px] uppercase tracking-wider mb-1">
            Duration
          </div>
          <div className="text-xl font-mono font-bold tabular-nums leading-none text-foreground">
            {duration}
          </div>
        </div>

        <div>
          <div className="text-muted-foreground text-[10px] uppercase tracking-wider mb-1">
            Tokens Used
          </div>
          <div className="text-xl font-mono font-bold tabular-nums leading-none text-foreground">
            {metrics.tokens_used.toLocaleString()}
          </div>
        </div>
      </div>
    </Card>
  )
}
