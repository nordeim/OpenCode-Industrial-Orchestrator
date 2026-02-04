/**
 * AGENT MARKETPLACE & REGISTRY
 * 
 * Browsing and managing specialized AI agents.
 * Supports internal and external (EAP) agents.
 */

"use client"

import { useState } from "react"
import Link from "next/link"
import { useAgents } from "@/lib/api/agents"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { RegisterAgentDialog } from "./RegisterAgentDialog"
import { Shield, Zap, Search, Activity, Cpu } from "lucide-react"

export default function AgentsPage() {
  const [isRegisterOpen, setIsRegisterOpen] = useState(false)
  const { data, isLoading, isError } = useAgents()

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight mb-2 font-mono uppercase">AGENT MARKETPLACE</h1>
          <p className="text-muted-foreground text-sm font-mono uppercase">
            Deploy and monitor specialized orchestration units
          </p>
        </div>
        <Button variant="accent" onClick={() => setIsRegisterOpen(true)}>
          + CONNECT EXTERNAL AGENT
        </Button>
      </header>

      {/* Registry Grid */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            [1, 2, 3].map(i => (
              <Card key={i} className="h-64 animate-pulse bg-muted/50" />
            ))
          ) : isError ? (
            <div className="col-span-full p-12 text-center border-2 border-dashed border-status-failed">
              <div className="text-status-failed font-bold uppercase mb-2 text-xl">REGISTRY CONNECTION ERROR</div>
              <p className="text-muted-foreground font-mono">Unable to retrieve agent registry from core orchestrator.</p>
            </div>
          ) : data?.items.length === 0 ? (
            <div className="col-span-full p-12 text-center border-2 border-dashed border-border">
              <div className="text-muted-foreground font-mono uppercase text-sm">NO AGENTS REGISTERED</div>
            </div>
          ) : (
            data?.items.map(agent => (
              <AgentCard key={agent.id} agent={agent} />
            ))
          )}
        </div>
      </section>

      <RegisterAgentDialog 
        isOpen={isRegisterOpen} 
        onClose={() => setIsRegisterOpen(false)} 
      />
    </div>
  )
}

function AgentCard({ agent }: { agent: any }) {
  const statusColors: Record<string, string> = {
    ACTIVE: "bg-status-running",
    IDLE: "bg-status-completed",
    BUSY: "bg-status-paused",
    DEGRADED: "bg-status-pending",
    OFFLINE: "bg-status-failed",
  }

  return (
    <Card className="flex flex-col h-full border-2 border-border p-0 overflow-hidden hover:border-accent transition-all hover:brutal-shadow-sm group">
      {/* Header */}
      <div className="p-4 border-b-2 border-border bg-muted/30 group-hover:bg-accent/5">
        <div className="flex items-center justify-between mb-2">
          <Badge variant="outline" className="font-mono text-[10px] border-border bg-background">
            {agent.type}
          </Badge>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 ${statusColors[agent.status]} ${agent.status === 'ACTIVE' ? 'animate-pulse' : ''}`} />
            <span className="text-[10px] font-bold font-mono text-muted-foreground uppercase">{agent.status}</span>
          </div>
        </div>
        <h3 className="text-lg font-bold font-mono truncate">{agent.name}</h3>
      </div>

      {/* Metrics */}
      <div className="p-4 flex-1 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-[10px] uppercase font-bold text-muted-foreground mb-1">SUCCESS RATE</div>
            <div className="text-xl font-bold font-mono tabular-nums">
              {(agent.success_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-muted-foreground mb-1">COMPLETED</div>
            <div className="text-xl font-bold font-mono tabular-nums">
              {agent.tasks_completed}
            </div>
          </div>
        </div>

        <div>
          <div className="text-[10px] uppercase font-bold text-muted-foreground mb-2">CAPABILITIES</div>
          <div className="flex flex-wrap gap-1.5">
            {agent.capabilities.slice(0, 3).map((cap: string) => (
              <span key={cap} className="text-[9px] px-1.5 py-0.5 border border-border bg-muted/50 font-mono">
                {cap.replace('_', ' ')}
              </span>
            ))}
            {agent.capabilities.length > 3 && (
              <span className="text-[9px] px-1.5 py-0.5 text-muted-foreground font-mono">
                +{agent.capabilities.length - 3} MORE
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t-2 border-border flex items-center justify-between">
        <div className="text-[10px] font-mono text-muted-foreground">
          LOAD: {(agent.current_load * 100).toFixed(0)}%
        </div>
        <Link href={`/agents/${agent.id}`}>
          <Button size="sm" variant="outline" className="h-7 text-[10px]">DIAGNOSTICS →</Button>
        </Link>
      </div>
    </Card>
  )
}
