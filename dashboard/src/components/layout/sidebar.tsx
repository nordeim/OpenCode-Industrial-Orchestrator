"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { setTenantId } from "@/lib/api/client";

/**
 * Navigation items for the industrial sidebar
 */
const NAV_ITEMS = [
    { href: "/", label: "OVERVIEW", icon: "◉" },
    { href: "/sessions", label: "SESSIONS", icon: "▣" },
    { href: "/agents", label: "AGENTS", icon: "◈" },
    { href: "/fine-tuning", label: "FINE-TUNING", icon: "⚙" },
    { href: "/tasks", label: "TASKS", icon: "◇" },
] as const;

/**
 * Industrial Sidebar Navigation
 * 
 * Features:
 * - Brutalist aesthetic with sharp edges
 * - Mono typography
 * - Active state indication
 * - Fixed positioning on desktop
 */
export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="hidden md:flex flex-col w-64 border-r-2 border-border bg-card">
            {/* Header */}
            <div className="p-6 border-b-2 border-border">
                <h1 className="text-lg font-bold tracking-tight">
                    <span className="text-accent">INDUSTRIAL</span>
                    <br />
                    ORCHESTRATOR
                </h1>
                
                {/* Tenant Selector */}
                <div className="mt-4">
                    <label className="text-[9px] font-bold text-muted-foreground uppercase block mb-1">Active Team</label>
                    <select 
                        onChange={(e) => setTenantId(e.target.value || null)}
                        className="w-full bg-background border-2 border-border text-xs font-mono p-1 focus:border-accent outline-none"
                    >
                        <option value="">System Default</option>
                        <option value="00000000-0000-0000-0000-000000000001">Alpha Team</option>
                        <option value="00000000-0000-0000-0000-000000000002">Beta Division</option>
                    </select>
                </div>

                <div className="mt-2 text-xs text-muted-foreground font-mono">
                    v0.2.0 // OPERATIONAL
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4">
                <ul className="space-y-1">
                    {NAV_ITEMS.map((item) => {
                        const isActive = pathname === item.href;

                        return (
                            <li key={item.href}>
                                <Link
                                    href={item.href}
                                    className={`
                    flex items-center gap-3 px-4 py-3 text-sm font-medium
                    border-2 transition-all duration-100
                    ${isActive
                                            ? "bg-accent text-accent-foreground border-accent brutal-shadow-sm"
                                            : "border-transparent hover:border-border hover:bg-muted"
                                        }
                  `}
                                >
                                    <span className="text-lg">{item.icon}</span>
                                    <span className="tracking-wide">{item.label}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            </nav>

            {/* Footer / Status */}
            <div className="p-4 border-t-2 border-border">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="inline-block w-2 h-2 bg-status-running animate-pulse"></span>
                    <span>SYSTEM NOMINAL</span>
                </div>
            </div>
        </aside>
    );
}

/**
 * Mobile Navigation Trigger
 * Shown only on small screens
 */
export function MobileNavTrigger() {
    return (
        <button
            type="button"
            className="md:hidden p-2 border-2 border-border bg-card hover:bg-muted"
            aria-label="Open navigation"
        >
            <span className="text-xl">☰</span>
        </button>
    );
}
