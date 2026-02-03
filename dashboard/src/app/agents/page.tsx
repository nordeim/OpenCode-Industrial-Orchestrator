/**
 * AGENTS PAGE
 * 
 * Agent monitoring dashboard with performance metrics.
 */

// Mock data
const MOCK_AGENTS = [
    {
        id: "1",
        name: "AGENT-BACKEND-001",
        type: "BACKEND",
        status: "ACTIVE",
        tier: "ELITE",
        load: 65,
        tasksCompleted: 42,
        successRate: 98.5,
    },
    {
        id: "2",
        name: "AGENT-FRONTEND-001",
        type: "FRONTEND",
        status: "ACTIVE",
        tier: "STANDARD",
        load: 40,
        tasksCompleted: 28,
        successRate: 95.2,
    },
    {
        id: "3",
        name: "AGENT-FULLSTACK-001",
        type: "FULLSTACK",
        status: "ACTIVE",
        tier: "ELITE",
        load: 80,
        tasksCompleted: 67,
        successRate: 99.1,
    },
    {
        id: "4",
        name: "AGENT-DEVOPS-001",
        type: "DEVOPS",
        status: "IDLE",
        tier: "STANDARD",
        load: 0,
        tasksCompleted: 15,
        successRate: 93.3,
    },
    {
        id: "5",
        name: "AGENT-QA-001",
        type: "QA",
        status: "DEGRADED",
        tier: "PROBATION",
        load: 20,
        tasksCompleted: 8,
        successRate: 75.0,
    },
];

export default function AgentsPage() {
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
                <div className="industrial-card">
                    <div className="text-muted-foreground text-xs mb-1">TOTAL AGENTS</div>
                    <div className="text-2xl font-bold tabular-nums">{MOCK_AGENTS.length}</div>
                </div>
                <div className="industrial-card">
                    <div className="text-muted-foreground text-xs mb-1">ACTIVE</div>
                    <div className="text-2xl font-bold tabular-nums text-status-running">
                        {MOCK_AGENTS.filter(a => a.status === "ACTIVE").length}
                    </div>
                </div>
                <div className="industrial-card">
                    <div className="text-muted-foreground text-xs mb-1">AVG. SUCCESS RATE</div>
                    <div className="text-2xl font-bold tabular-nums">
                        {(MOCK_AGENTS.reduce((sum, a) => sum + a.successRate, 0) / MOCK_AGENTS.length).toFixed(1)}%
                    </div>
                </div>
                <div className="industrial-card">
                    <div className="text-muted-foreground text-xs mb-1">TOTAL TASKS</div>
                    <div className="text-2xl font-bold tabular-nums">
                        {MOCK_AGENTS.reduce((sum, a) => sum + a.tasksCompleted, 0)}
                    </div>
                </div>
            </section>

            {/* Agent Cards Grid */}
            <section>
                <h2 className="text-label mb-4">REGISTERED AGENTS</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {MOCK_AGENTS.map((agent) => (
                        <AgentCard key={agent.id} agent={agent} />
                    ))}
                </div>
            </section>
        </div>
    );
}

interface Agent {
    id: string;
    name: string;
    type: string;
    status: string;
    tier: string;
    load: number;
    tasksCompleted: number;
    successRate: number;
}

function AgentCard({ agent }: { agent: Agent }) {
    const statusColors: Record<string, string> = {
        ACTIVE: "bg-status-running",
        IDLE: "bg-status-pending",
        DEGRADED: "bg-status-failed",
    };

    const tierColors: Record<string, string> = {
        ELITE: "text-status-completed",
        STANDARD: "text-foreground",
        PROBATION: "text-status-failed",
    };

    return (
        <div className="industrial-card">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
                <div>
                    <h3 className="font-bold text-sm">{agent.name}</h3>
                    <div className="text-xs text-muted-foreground">{agent.type}</div>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 ${statusColors[agent.status]} ${agent.status === "ACTIVE" ? "animate-pulse" : ""}`}></span>
                    <span className="text-xs uppercase">{agent.status}</span>
                </div>
            </div>

            {/* Load Gauge */}
            <div className="mb-4">
                <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">LOAD</span>
                    <span className="tabular-nums">{agent.load}%</span>
                </div>
                <div className="h-2 bg-muted">
                    <div
                        className={`h-full ${agent.load > 80 ? "bg-status-failed" : agent.load > 50 ? "bg-status-pending" : "bg-status-running"}`}
                        style={{ width: `${agent.load}%` }}
                    ></div>
                </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <div className="text-muted-foreground text-xs">TIER</div>
                    <div className={`font-bold ${tierColors[agent.tier]}`}>{agent.tier}</div>
                </div>
                <div>
                    <div className="text-muted-foreground text-xs">SUCCESS RATE</div>
                    <div className="font-bold tabular-nums">{agent.successRate}%</div>
                </div>
                <div>
                    <div className="text-muted-foreground text-xs">TASKS COMPLETED</div>
                    <div className="font-bold tabular-nums">{agent.tasksCompleted}</div>
                </div>
            </div>
        </div>
    );
}
