/**
 * AGENT DIAGNOSTICS PAGE
 * 
 * Detailed monitoring for a single agent unit.
 * Shows heartbeat logs, capability details, and performance trends.
 */

"use client"

import { useAgent } from "@/lib/api/agents"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Activity, Shield, Zap, Terminal, Clock, BarChart3 } from "lucide-react"

export default function AgentDiagnosticsPage() {
  const { id } = useParams()
  const { data: agent, isLoading, isError } = useAgent(id as string)

  if (isLoading) return <div className="p-8 font-mono animate-pulse">LOADING DIAGNOSTICS...</div>
  if (isError || !agent) return <div className="p-8 text-status-failed font-mono uppercase">ERROR: DIAGNOSTIC UNIT OFFLINE</div>

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Breadcrumbs */}
      <nav className="mb-6 flex gap-2 text-xs font-mono text-muted-foreground uppercase">
        <Link href="/agents" className="hover:text-accent">AGENTS</Link>
        <span>/</span>
        <span className="text-foreground">{agent.name}</span>
      </nav>

      {/* Header */}
      <header className="mb-8 flex items-end justify-between border-b-2 border-border pb-6">
        <div className="flex gap-6 items-center">
          <div className="w-16 h-16 border-2 border-border bg-muted flex items-center justify-center">
            <Activity className={`h-8 w-8 ${agent.status === 'ACTIVE' ? 'text-status-running animate-pulse' : 'text-muted-foreground'}`} />
          </div>
          <div>
            <h1 className="text-3xl font-bold font-mono tracking-tighter mb-1 uppercase">{agent.name}</h1>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="font-mono">{agent.type}</Badge>
              <div className="flex items-center gap-1.5 text-xs font-mono text-muted-foreground uppercase">
                <span className={`w-2 h-2 ${agent.status === 'ACTIVE' ? 'bg-status-running' : 'bg-muted'}`} />
                {agent.status} // VERSION {agent.id.split('-')[0]}
              </div>
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm">RESET METRICS</Button>
          <Button variant="destructive" size="sm">DEREGISTER UNIT</Button>
        </div>
      </header>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column: Performance */}
        <div className="col-span-2 space-y-6">
          <section className="grid grid-cols-3 gap-4">
            <MetricBox label="SUCCESS RATE" value={`${(agent.success_rate * 100).toFixed(1)}%`} sub="Aggregate Score" />
            <MetricBox label="TASKS COMPLETED" value={agent.tasks_completed.toString()} sub="Lifetime Total" />
            <MetricBox label="CURRENT LOAD" value={`${(agent.current_load * 100).toFixed(0)}%`} sub={`${agent.max_concurrent_tasks} Max Capacity`} />
          </section>

          <Card className="p-6">
            <div className="flex items-center gap-2 mb-6">
              <Terminal className="h-4 w-4 text-accent" />
              <h2 className="text-sm font-bold uppercase font-mono">CAPABILITY MANIFEST</h2>
            </div>
            <div className="grid grid-cols-2 gap-y-4 gap-x-8 font-mono">
              {agent.capabilities.map(cap => (
                <div key={cap} className="flex items-center justify-between border-b border-border pb-2">
                  <span className="text-xs uppercase text-muted-foreground">{cap.replace('_', ' ')}</span>
                  <Badge className="h-5 text-[9px] bg-status-running/10 text-status-running border-status-running">ACTIVE</Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 h-64 flex items-center justify-center border-dashed border-2">
            <div className="text-center text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-20" />
              <p className="text-xs font-mono uppercase">Performance telemetry graph pending</p>
            </div>
          </Card>
        </div>

        {/* Right Column: Details & Status */}
        <div className="space-y-6">
          <Card className="p-6 bg-muted/20">
            <h2 className="text-sm font-bold uppercase font-mono mb-4 flex items-center gap-2">
              <Clock className="h-4 w-4" /> HEALTH CHECK
            </h2>
            <div className="space-y-4 font-mono">
              <div>
                <span className="text-[10px] text-muted-foreground block uppercase">Last Heartbeat</span>
                <span className="text-sm tabular-nums">{new Date(agent.last_heartbeat).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[10px] text-muted-foreground block uppercase">Registration Date</span>
                <span className="text-sm tabular-nums">{new Date(agent.registered_at).toLocaleString()}</span>
              </div>
              <div className="pt-4 border-t border-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-muted-foreground uppercase">Network Latency</span>
                  <span className="text-sm tabular-nums text-status-running">24ms</span>
                </div>
                <div className="w-full bg-border h-1">
                  <div className="bg-status-running h-full w-[24%]" />
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-sm font-bold uppercase font-mono mb-4 flex items-center gap-2">
              <Shield className="h-4 w-4 text-status-pending" /> PERFORMANCE TIER
            </h2>
            <div className="text-center py-4">
              <div className="text-4xl font-black text-accent mb-1 italic tracking-tighter uppercase">{agent.tier}</div>
              <p className="text-[10px] text-muted-foreground uppercase">Classified Deployment Tier</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

function MetricBox({ label, value, sub }: { label: string, value: string, sub: string }) {
  return (
    <Card className="p-4 bg-card hover:border-accent transition-colors">
      <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">{label}</div>
      <div className="text-2xl font-bold font-mono tracking-tighter">{value}</div>
      <div className="text-[9px] text-muted-foreground uppercase mt-1">{sub}</div>
    </Card>
  )
}
