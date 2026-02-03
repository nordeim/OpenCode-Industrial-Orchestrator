/**
 * TASKS PAGE
 * 
 * Task decomposition tree and dependency tracking.
 * Connected to Industrial Orchestrator API.
 */

"use client"

import { useState } from "react"
import { useTasks } from "@/lib/api/tasks"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Task, TaskStatus, TaskComplexity } from "@/lib/api/types"

const COMPLEXITY_FILTERS: (TaskComplexity | "ALL")[] = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

export default function TasksPage() {
  const [complexityFilter, setComplexityFilter] = useState<TaskComplexity | undefined>(undefined)
  
  // Fetch root tasks (tasks without parents)
  // Note: API should support recursive expansion or we fetch children on demand
  // For this implementation, we'll fetch all and build tree client-side for smaller datasets,
  // or rely on the API returning a flat list that we restructure.
  // Assuming API returns flat list.
  const { data, isLoading, isError } = useTasks({
    // We might want to filter by session eventually
  })

  const handleFilterChange = (filter: TaskComplexity | "ALL") => {
    setComplexityFilter(filter === "ALL" ? undefined : filter)
  }

  // Client-side tree construction
  const rootTasks = data?.items.filter(t => !t.parent_task_id) || []
  
  // Filter roots by complexity if selected
  const filteredRoots = complexityFilter 
    ? rootTasks.filter(t => t.complexity === complexityFilter)
    : rootTasks

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight mb-2 font-mono">TASKS</h1>
        <p className="text-muted-foreground text-sm font-mono">
          Task decomposition tree and dependency tracking
        </p>
      </header>

      {/* Filters */}
      <section className="mb-6">
        <div className="flex gap-2 flex-wrap">
          {COMPLEXITY_FILTERS.map((filter) => (
            <button
              key={filter}
              onClick={() => handleFilterChange(filter)}
              className={`
                px-3 py-1.5 text-xs font-semibold uppercase tracking-wider
                border-2 transition-all font-mono
                ${(filter === "ALL" && !complexityFilter) || filter === complexityFilter
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

      {/* Task Tree */}
      <section>
        <h2 className="text-label mb-4">TASK HIERARCHY</h2>
        <div className="space-y-4">
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-24 bg-muted/50 animate-pulse border-l-4 border-muted" />
              ))}
            </div>
          ) : isError ? (
            <Card className="border-status-failed bg-status-failed/5 p-8 text-center">
              <div className="text-status-failed font-bold">FAILED TO LOAD TASKS</div>
            </Card>
          ) : filteredRoots.length === 0 ? (
            <Card className="p-12 text-center text-muted-foreground border-dashed">
              NO TASKS FOUND
            </Card>
          ) : (
            filteredRoots.map((task) => (
              <TaskTreeNode
                key={task.id}
                task={task}
                allTasks={data?.items || []}
                level={0}
              />
            ))
          )}
        </div>
      </section>
    </div>
  )
}

function TaskTreeNode({
  task,
  allTasks,
  level
}: {
  task: Task
  allTasks: Task[]
  level: number
}) {
  const subtasks = allTasks.filter(t => t.parent_task_id === task.id)
  const hasSubtasks = subtasks.length > 0

  const statusColors: Record<string, string> = {
    COMPLETED: "border-l-status-completed",
    IN_PROGRESS: "border-l-status-running",
    PENDING: "border-l-status-pending",
    FAILED: "border-l-status-failed",
    BLOCKED: "border-l-status-failed", // Or warning
    QUEUED: "border-l-muted",
    CANCELLED: "border-l-muted",
  }

  const complexityColors: Record<string, string> = {
    LOW: "text-muted-foreground",
    MEDIUM: "text-foreground",
    HIGH: "text-status-pending",
    CRITICAL: "text-status-failed font-bold",
  }

  return (
    <div className={level > 0 ? "ml-6" : ""}>
      <Card className={`border-l-4 ${statusColors[task.status] || "border-l-border"}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              {hasSubtasks && (
                <span className="text-muted-foreground text-[10px]">▼</span>
              )}
              <h3 className="font-bold text-sm font-mono">{task.title}</h3>
            </div>
            <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
              <span>ID: {task.id.split('-')[0]}...</span>
              <span>Session: {task.session_id.split('-')[0]}...</span>
              {hasSubtasks && (
                <span>
                  Subtasks: {task.completed_subtasks}/{task.subtask_count}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className={`text-[10px] uppercase font-mono ${complexityColors[task.complexity]}`}>
              {task.complexity}
            </span>
            <TaskStatusBadge status={task.status} />
          </div>
        </div>

        {/* Progress bar for parent tasks */}
        {hasSubtasks && (
          <div className="mt-4">
            <div className="flex justify-between text-[10px] mb-1 font-mono">
              <span className="text-muted-foreground">PROGRESS</span>
              <span className="tabular-nums">
                {task.subtask_count > 0
                  ? Math.round((task.completed_subtasks / task.subtask_count) * 100)
                  : 0}%
              </span>
            </div>
            <div className="h-1.5 bg-muted w-full">
              <div
                className="h-full bg-status-completed transition-all duration-500"
                style={{
                  width: `${task.subtask_count > 0
                    ? (task.completed_subtasks / task.subtask_count) * 100
                    : 0}%`
                }}
              />
            </div>
          </div>
        )}
      </Card>

      {/* Recursive render */}
      {hasSubtasks && (
        <div className="mt-2 space-y-2">
          {subtasks.map((subtask) => (
            <TaskTreeNode
              key={subtask.id}
              task={subtask}
              allTasks={allTasks}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function TaskStatusBadge({ status }: { status: TaskStatus }) {
  const statusStyles: Record<string, string> = {
    COMPLETED: "bg-status-completed/20 text-status-completed border-status-completed",
    IN_PROGRESS: "bg-status-running/20 text-status-running border-status-running",
    PENDING: "bg-status-pending/20 text-status-pending border-status-pending",
    FAILED: "bg-status-failed/20 text-status-failed border-status-failed",
    BLOCKED: "bg-status-failed/10 text-status-failed border-status-failed",
    QUEUED: "bg-muted text-muted-foreground border-border",
    CANCELLED: "bg-transparent text-muted-foreground border-border dashed",
  }

  return (
    <Badge className={`border ${statusStyles[status] || "bg-muted text-muted-foreground border-border"}`}>
      {status.replace("_", " ")}
    </Badge>
  )
}