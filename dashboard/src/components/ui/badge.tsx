import * as React from "react"

const badgeVariants = {
  default: "bg-muted text-muted-foreground border-border",
  success: "bg-status-running/20 text-status-running border-status-running",
  warning: "bg-status-pending/20 text-status-pending border-status-pending",
  error: "bg-status-failed/20 text-status-failed border-status-failed",
  neutral: "bg-card text-foreground border-border",
  outline: "bg-transparent border-foreground/20 text-foreground",
}

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: keyof typeof badgeVariants
}

export function Badge({ 
  className = "", 
  variant = "default", 
  ...props 
}: BadgeProps) {
  return (
    <span 
      className={`
        inline-flex items-center px-2.5 py-0.5 
        text-xs font-semibold font-mono uppercase tracking-wider
        border ${badgeVariants[variant]} 
        ${className}
      `} 
      {...props} 
    />
  )
}
