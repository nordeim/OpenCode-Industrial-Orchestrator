/**
 * TRAINING JOB DIAGNOSTICS
 */

"use client"

import { useFineTuningJob, useStartFineTuningJob } from "@/lib/api/fine-tuning"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Activity, Database, Sparkles, AlertTriangle, ArrowLeft, Clock, Zap } from "lucide-react"

export default function FineTuningJobDetailsPage() {
  const { id } = useParams()
  const { data: job, isLoading, isError } = useFineTuningJob(id as string)
  const startMutation = useStartFineTuningJob()

  if (isLoading) return <div className="p-8 font-mono animate-pulse uppercase">Retrieving Job Parameters...</div>
  if (isError || !job) return <div className="p-8 text-status-failed font-mono uppercase">Error: Training Unit Desynchronized</div>

  const handleStart = async () => {
    await startMutation.mutateAsync({ id: job.id, datasetDir: "/data/datasets" })
  }

  const progress = (job.metadata?.progress as number) || 0

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <Link href="/fine-tuning" className="flex items-center gap-2 text-xs font-mono text-muted-foreground hover:text-accent mb-6 uppercase">
        <ArrowLeft className="h-3 w-3" /> Back to Registry
      </Link>

      <header className="mb-8 flex items-end justify-between border-b-2 border-border pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold font-mono tracking-tighter uppercase">{job.target_model_name}</h1>
            <Badge variant="outline" className="font-mono uppercase text-[10px]">Job {job.id.split('-')[0]}</Badge>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground uppercase">
            <span>BASE: {job.base_model}</span>
            <span className="flex items-center gap-1">
              <div className={`w-2 h-2 ${job.status === 'running' ? 'bg-status-running animate-pulse' : 'bg-muted'}`} />
              STATUS: {job.status}
            </span>
          </div>
        </div>
        <div className="flex gap-3">
          {job.status === 'pending' && (
            <Button variant="accent" onClick={handleStart} disabled={startMutation.isPending}>
              {startMutation.isPending ? "CURATING..." : "START PIPELINE"}
            </Button>
          )}
          <Button variant="destructive">CANCEL JOB</Button>
        </div>
      </header>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          {/* Progress Section */}
          {job.status === 'running' && (
            <Card className="p-6 border-status-running/50 bg-status-running/5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-bold font-mono uppercase flex items-center gap-2">
                  <Activity className="h-4 w-4 text-status-running animate-pulse" /> Training Progress
                </h2>
                <span className="text-xs font-mono text-status-running font-bold">{(progress * 100).toFixed(1)}%</span>
              </div>
              <Progress value={progress * 100} className="h-2 bg-muted border border-border" />
              <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                <div className="p-3 border border-border bg-background">
                  <div className="text-[9px] font-bold text-muted-foreground uppercase">Current Loss</div>
                  <div className="text-sm font-mono tabular-nums">0.2451</div>
                </div>
                <div className="p-3 border border-border bg-background">
                  <div className="text-[9px] font-bold text-muted-foreground uppercase">Step</div>
                  <div className="text-sm font-mono tabular-nums">1,420 / 5,000</div>
                </div>
                <div className="p-3 border border-border bg-background">
                  <div className="text-[9px] font-bold text-muted-foreground uppercase">Time Remaining</div>
                  <div className="text-sm font-mono uppercase">04:12:00</div>
                </div>
              </div>
            </Card>
          )}

          {/* Dataset Metrics */}
          <section className="grid grid-cols-3 gap-4">
            <MetricTile label="SAMPLES" value={job.sample_count.toString()} icon={<Database className="h-3 w-3" />} />
            <MetricTile label="BATCH SIZE" value="4" icon={<Zap className="h-3 w-3 text-accent" />} />
            <MetricTile label="EPOCHS" value="3" icon={<Clock className="h-3 w-3" />} />
          </section>

          {/* Logs Terminal */}
          <Card className="p-0 bg-black border-2 border-border overflow-hidden">
            <div className="p-2 bg-muted flex items-center justify-between border-b border-border">
              <span className="text-[10px] font-bold font-mono uppercase text-muted-foreground ml-2">Training Logs</span>
              <div className="flex gap-1.5 mr-2">
                <div className="w-2 h-2 bg-status-failed/50" />
                <div className="w-2 h-2 bg-status-pending/50" />
                <div className="w-2 h-2 bg-status-running/50" />
              </div>
            </div>
            <div className="p-4 font-mono text-[11px] h-64 overflow-auto text-green-500/80 leading-relaxed">
              <p>[SYSTEM] Initializing weight allocation...</p>
              <p>[DATA] Loaded dataset from {job.dataset_path || 'PENDING'}</p>
              <p>[TRAIN] Epoch 1/3: 100% |██████████| Loss: 0.42</p>
              {job.status === 'running' && (
                <p className="animate-pulse">[TRAIN] Epoch 2/3: 24% |███.......| Loss: 0.24</p>
              )}
              {job.status === 'completed' && (
                <>
                  <p>[TRAIN] Epoch 3/3: 100% |██████████| Loss: 0.12</p>
                  <p>[EVAL] benchmarking against Industrial Test Suite...</p>
                  <p className="text-accent font-bold">[FINISH] Model specialized successfully.</p>
                </>
              )}
            </div>
          </Card>
        </div>

        {/* Info Column */}
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xs font-bold uppercase font-mono mb-4">Pipeline Origin</h2>
            <div className="space-y-4 font-mono text-[11px]">
              <div>
                <span className="text-muted-foreground block uppercase mb-1">Created At</span>
                <span>{new Date(job.created_at).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-muted-foreground block uppercase mb-1">Dataset Source</span>
                <span className="truncate block text-accent">SUCCESS_LOGS_MIN_0.9</span>
              </div>
            </div>
          </Card>

          {job.error_message && (
            <Card className="p-6 border-status-failed bg-status-failed/5">
              <h2 className="text-xs font-bold uppercase font-mono mb-2 text-status-failed flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" /> Pipeline Failure
              </h2>
              <p className="text-[11px] font-mono text-status-failed leading-relaxed">
                {job.error_message}
              </p>
            </Card>
          )}

          <div className="p-6 border-2 border-dashed border-border flex flex-col items-center text-center justify-center h-48">
            <Sparkles className="h-8 w-8 text-muted-foreground opacity-20 mb-3" />
            <p className="text-[10px] font-mono uppercase text-muted-foreground">Automated Promotion Lock</p>
            <p className="text-[9px] font-mono text-muted-foreground/60 mt-1 uppercase">Model will be automatically promoted to ELITE tier after passing evaluation.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricTile({ label, value, icon }: { label: string, value: string, icon: React.ReactNode }) {
  return (
    <Card className="p-4 border-2 border-border">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-[10px] font-bold text-muted-foreground uppercase">{label}</span>
      </div>
      <div className="text-2xl font-bold font-mono tracking-tighter">{value}</div>
    </Card>
  )
}
