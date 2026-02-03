/**
 * AGENTS DASHBOARD
 * 
 * Monitor agent performance and manage registrations.
 * Connected to Industrial Orchestrator API.
 */

"use client"

import { useAgents, useAgentPerformance } from "@/lib/api/agents"
import { Card } from "@/components/ui/card"
import type { Agent } from "@/lib/api/types"

export default function AgentsPage() {
  // Data Fetching
  const { 
    data: agentsData, 
    isLoading: isAgentsLoading,
    isError: isAgentsError 
  } = useAgents()

  const {
    data: perfData,
    isLoading: isPerfLoading
  } = useAgentPerformance()

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight mb-2">AGENTS</h1>
          <p className="text-muted-foreground text-sm">
            Monitor agent performance and manage registrations
          </p>
        </div>
        <button className="btn-industrial">
          + REGISTER AGENT
        </button>
      </header>

      {/* Summary Cards */}
      <section className="mb-8 grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard 
          label="TOTAL AGENTS" 
          value={perfData?.total_agents ?? 0}
          loading={isPerfLoading} 
        />
        <SummaryCard 
          label="ACTIVE" 
          value={perfData?.active_agents ?? 0} 
          loading={isPerfLoading}
          highlight
        />
        <SummaryCard 
          label="AVG. SUCCESS RATE" 
          value={`${perfData?.avg_success_rate.toFixed(1) ?? 0}%`} 
          loading={isPerfLoading} 
        />
        <SummaryCard 
          label="TOTAL TASKS" 
          value={perfData?.total_tasks_completed ?? 0} 
          loading={isPerfLoading} 
        />
      </section>

      {/* Agent Cards Grid */}
      <section>
        <h2 className="text-label mb-4">REGISTERED AGENTS</h2>
        
        {isAgentsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-muted/50 animate-pulse border-2 border-border" />
            ))}
          </div>
        ) : isAgentsError ? (
          <Card className="border-status-failed bg-status-failed/5 p-8 text-center">
            <div className="text-status-failed font-bold">FAILED TO LOAD AGENTS</div>
          </Card>
        ) : agentsData?.items.length === 0 ? (
          <Card className="p-12 text-center text-muted-foreground border-dashed">
            NO AGENTS REGISTERED
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agentsData?.items.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function SummaryCard({ 
  label, 
  value, 
  loading, 
  highlight 
}: { 
  label: string, 
  value: string | number, 
  loading: boolean, 
  highlight?: boolean 
}) {
  return (
    <Card className="flex flex-col justify-center">
      <div className="text-muted-foreground text-[10px] uppercase tracking-wider mb-1">
        {label}
      </div>
      {loading ? (
        <div className="h-8 w-16 bg-muted animate-pulse" />
      ) : (
        <div className={`text-2xl font-bold tabular-nums font-mono ${highlight ? 'text-status-running' : 'text-foreground'}`}>
          {value}
        </div>
      )}
    </Card>
  )
}

function AgentCard({ agent }: { agent: Agent }) {
  const statusColors: Record<string, string> = {
    ACTIVE: "bg-status-running",
    IDLE: "bg-status-pending",
    BUSY: "bg-status-completed",
    DEGRADED: "bg-status-failed",
    OFFLINE: "bg-muted-foreground",
  }

  const tierColors: Record<string, string> = {
    ELITE: "text-status-completed",
    STANDARD: "text-foreground",
    PROBATION: "text-status-failed",
  }

  return (
    <Card className="hover:border-accent transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-bold text-sm font-mono">{agent.name}</h3>
          <div className="text-[10px] font-mono text-muted-foreground mt-1">{agent.type}</div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 ${statusColors[agent.status]} ${agent.status === "ACTIVE" ? "animate-pulse" : ""}`}></span>
          <span className="text-[10px] font-mono uppercase text-muted-foreground">{agent.status}</span>
        </div>
      </div>

      {/* Load Gauge */}
      <div className="mb-4">
        <div className="flex justify-between text-[10px] mb-1 font-mono">
          <span className="text-muted-foreground">LOAD</span>
          <span className="tabular-nums">{agent.current_load}%</span>
        </div>
        <div className="h-1.5 bg-muted w-full">
          <div
            className={`h-full transition-all duration-500 ${
              agent.current_load > 80 ? "bg-status-failed" : 
              agent.current_load > 50 ? "bg-status-pending" : "bg-status-running"
            }`}
            style={{ width: `${agent.current_load}%` }}
          />
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 text-xs font-mono pt-4 border-t border-border/50">
        <div>
          <div className="text-muted-foreground text-[10px] uppercase">TIER</div>
          <div className={`font-bold ${tierColors[agent.tier]}`}>{agent.tier}</div>
        </div>
        <div>
          <div className="text-muted-foreground text-[10px] uppercase">SUCCESS RATE</div>
          <div className="font-bold tabular-nums">{agent.success_rate}%</div>
        </div>
        <div>
          <div className="text-muted-foreground text-[10px] uppercase">TASKS</div>
          <div className="font-bold tabular-nums">{agent.tasks_completed}</div>
        </div>
        <div>
          <div className="text-muted-foreground text-[10px] uppercase">CAPABILITY</div>
          <div className="font-bold tabular-nums">{agent.capabilities.length}</div>
        </div>
      </div>
    </Card>
  )
}