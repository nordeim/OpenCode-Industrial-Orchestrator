import * as React from "react"

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  action?: React.ReactNode
}

export function Card({ 
  className = "", 
  title, 
  action,
  children, 
  ...props 
}: CardProps) {
  return (
    <div 
      className={`industrial-card ${className}`} 
      {...props}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-border/50">
          {title && (
            <h3 className="text-sm font-bold tracking-tight text-muted-foreground uppercase">
              {title}
            </h3>
          )}
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
