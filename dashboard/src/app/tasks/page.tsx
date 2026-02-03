/**
 * TASKS PAGE
 * 
 * Task decomposition and dependency visualization.
 */

// Mock data
const MOCK_TASKS = [
    {
        id: "1",
        title: "Implement User Authentication",
        status: "IN_PROGRESS",
        complexity: "HIGH",
        sessionId: "1",
        parentId: null,
        subtaskCount: 3,
        completedSubtasks: 1,
    },
    {
        id: "2",
        title: "Setup JWT Token Generation",
        status: "COMPLETED",
        complexity: "MEDIUM",
        sessionId: "1",
        parentId: "1",
        subtaskCount: 0,
        completedSubtasks: 0,
    },
    {
        id: "3",
        title: "Create Login API Endpoint",
        status: "IN_PROGRESS",
        complexity: "MEDIUM",
        sessionId: "1",
        parentId: "1",
        subtaskCount: 0,
        completedSubtasks: 0,
    },
    {
        id: "4",
        title: "Implement Password Hashing",
        status: "PENDING",
        complexity: "LOW",
        sessionId: "1",
        parentId: "1",
        subtaskCount: 0,
        completedSubtasks: 0,
    },
    {
        id: "5",
        title: "Build Dashboard UI",
        status: "PENDING",
        complexity: "HIGH",
        sessionId: "2",
        parentId: null,
        subtaskCount: 5,
        completedSubtasks: 0,
    },
];

const COMPLEXITY_FILTERS = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function TasksPage() {
    const rootTasks = MOCK_TASKS.filter(t => t.parentId === null);

    return (
        <div className="p-8">
            {/* Header */}
            <header className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight mb-2">TASKS</h1>
                <p className="text-muted-foreground text-sm">
                    Task decomposition tree and dependency tracking
                </p>
            </header>

            {/* Filters */}
            <section className="mb-6">
                <div className="flex gap-2 flex-wrap">
                    {COMPLEXITY_FILTERS.map((filter) => (
                        <button
                            key={filter}
                            className={`
                px-3 py-1.5 text-xs font-semibold uppercase tracking-wider
                border-2 transition-all
                ${filter === "ALL"
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
                    {rootTasks.map((task) => (
                        <TaskTreeNode
                            key={task.id}
                            task={task}
                            allTasks={MOCK_TASKS}
                            level={0}
                        />
                    ))}
                </div>
            </section>
        </div>
    );
}

interface Task {
    id: string;
    title: string;
    status: string;
    complexity: string;
    sessionId: string;
    parentId: string | null;
    subtaskCount: number;
    completedSubtasks: number;
}

function TaskTreeNode({
    task,
    allTasks,
    level
}: {
    task: Task;
    allTasks: Task[];
    level: number;
}) {
    const subtasks = allTasks.filter(t => t.parentId === task.id);
    const hasSubtasks = subtasks.length > 0;

    const statusColors: Record<string, string> = {
        COMPLETED: "border-l-status-completed",
        IN_PROGRESS: "border-l-status-running",
        PENDING: "border-l-status-pending",
        FAILED: "border-l-status-failed",
    };

    const complexityColors: Record<string, string> = {
        LOW: "text-muted-foreground",
        MEDIUM: "text-foreground",
        HIGH: "text-status-pending",
        CRITICAL: "text-status-failed",
    };

    return (
        <div className={level > 0 ? "ml-6" : ""}>
            <div className={`industrial-card border-l-4 ${statusColors[task.status] || "border-l-border"}`}>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                            {hasSubtasks && (
                                <span className="text-muted-foreground">▼</span>
                            )}
                            <h3 className="font-bold text-sm">{task.title}</h3>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>ID: {task.id}</span>
                            <span>Session: {task.sessionId}</span>
                            {hasSubtasks && (
                                <span>
                                    Subtasks: {task.completedSubtasks}/{task.subtaskCount}
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className={`text-xs font-semibold uppercase ${complexityColors[task.complexity]}`}>
                            {task.complexity}
                        </span>
                        <TaskStatusBadge status={task.status} />
                    </div>
                </div>

                {/* Progress bar for parent tasks */}
                {hasSubtasks && (
                    <div className="mt-4">
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-muted-foreground">PROGRESS</span>
                            <span className="tabular-nums">
                                {task.subtaskCount > 0
                                    ? Math.round((task.completedSubtasks / task.subtaskCount) * 100)
                                    : 0}%
                            </span>
                        </div>
                        <div className="h-1.5 bg-muted">
                            <div
                                className="h-full bg-status-completed"
                                style={{
                                    width: `${task.subtaskCount > 0
                                        ? (task.completedSubtasks / task.subtaskCount) * 100
                                        : 0}%`
                                }}
                            ></div>
                        </div>
                    </div>
                )}
            </div>

            {/* Render subtasks */}
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
    );
}

function TaskStatusBadge({ status }: { status: string }) {
    const statusStyles: Record<string, string> = {
        COMPLETED: "bg-status-completed/20 text-status-completed border-status-completed",
        IN_PROGRESS: "bg-status-running/20 text-status-running border-status-running",
        PENDING: "bg-status-pending/20 text-status-pending border-status-pending",
        FAILED: "bg-status-failed/20 text-status-failed border-status-failed",
    };

    return (
        <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold border uppercase tracking-wider ${statusStyles[status] || "bg-muted text-muted-foreground border-border"}`}>
            {status.replace("_", " ")}
        </span>
    );
}
