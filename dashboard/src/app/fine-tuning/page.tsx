/**
 * FINE-TUNING PIPELINE MANAGEMENT
 */

"use client"

import { useState } from "react"
import Link from "next/link"
import { useFineTuningJobs, usePollFineTuningJobs } from "@/lib/api/fine-tuning"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Activity, Database, Sparkles, RefreshCcw } from "lucide-react"

export default function FineTuningPage() {
  const { data: jobs, isLoading, isError } = useFineTuningJobs()
  const pollMutation = usePollFineTuningJobs()

  const handlePoll = async () => {
    await pollMutation.mutateAsync()
  }

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight mb-2 font-mono uppercase">MODEL REGISTRY</h1>
          <p className="text-muted-foreground text-sm font-mono uppercase">
            Autonomous feedback loop & LLM specialization pipeline
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handlePoll} disabled={pollMutation.isPending}>
            <RefreshCcw className={`h-4 w-4 mr-2 ${pollMutation.isPending ? 'animate-spin' : ''}`} />
            SYNC STATUS
          </Button>
          <Link href="/fine-tuning/new">
            <Button variant="accent">
              + NEW TRAINING JOB
            </Button>
          </Link>
        </div>
      </header>

      {/* Jobs Table */}
      <section>
        <Card className="p-0 overflow-hidden min-h-[400px]">
          {isLoading ? (
            <div className="p-12 space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-12 bg-muted/50 animate-pulse" />
              ))}
            </div>
          ) : isError ? (
            <div className="p-12 text-center border-2 border-dashed border-status-failed m-6">
              <div className="text-status-failed font-bold uppercase mb-2 text-xl">PIPELINE OFFLINE</div>
              <p className="text-muted-foreground font-mono">Unable to connect to fine-tuning orchestration service.</p>
            </div>
          ) : !jobs || jobs.length === 0 ? (
            <div className="p-24 text-center">
              <div className="w-16 h-16 border-2 border-dashed border-border flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-8 w-8 text-muted-foreground opacity-20" />
              </div>
              <div className="text-muted-foreground font-mono uppercase text-sm">NO ACTIVE TRAINING JOBS</div>
              <p className="text-xs text-muted-foreground/60 mt-2 font-mono">Collect high-quality session logs to specialize your models.</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-border bg-muted">
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider font-mono">Target Model</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider font-mono">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider font-mono">Samples</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wider font-mono">Started</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-wider font-mono">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="border-b border-border hover:bg-muted transition-colors group">
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="font-bold font-mono text-sm uppercase">{job.target_model_name}</span>
                        <span className="text-[10px] text-muted-foreground font-mono italic">BASE: {job.base_model}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="px-4 py-3 text-sm font-mono tabular-nums">
                      {job.sample_count}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground font-mono uppercase">
                      {job.started_at ? new Date(job.started_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link href={`/fine-tuning/${job.id}`}>
                        <Button variant="outline" size="sm" className="h-7 text-[10px]">DETAILS</Button>
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

function StatusBadge({ status }: { status: string }) {
  const statusStyles: Record<string, string> = {
    running: "bg-status-running/20 text-status-running border-status-running",
    pending: "bg-status-pending/20 text-status-pending border-status-pending",
    completed: "bg-status-completed/20 text-status-completed border-status-completed",
    failed: "bg-status-failed/20 text-status-failed border-status-failed",
    queued: "bg-status-paused/20 text-status-paused border-status-paused",
    evaluating: "bg-accent/20 text-accent border-accent",
  }

  return (
    <Badge className={`border uppercase font-mono text-[9px] ${statusStyles[status] || "bg-muted text-muted-foreground border-border"}`}>
      {status === 'running' ? (
        <span className="flex items-center gap-1">
          <Activity className="h-2 w-2 animate-pulse" />
          {status}
        </span>
      ) : status}
    </Badge>
  )
}
