import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "accent" | "destructive"
  size?: "default" | "sm" | "lg" | "icon"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap text-sm font-bold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 font-mono uppercase tracking-wider",
          {
            "bg-foreground text-background border-2 border-foreground hover:bg-background hover:text-foreground": variant === "default",
            "border-2 border-border bg-transparent hover:border-accent hover:text-accent": variant === "outline",
            "hover:bg-muted hover:text-accent border-2 border-transparent": variant === "ghost",
            "bg-accent text-accent-foreground border-2 border-accent hover:bg-background hover:text-accent brutal-shadow-sm active:translate-x-[2px] active:translate-y-[2px] active:shadow-none": variant === "accent",
            "bg-status-failed text-white border-2 border-status-failed hover:bg-background hover:text-status-failed": variant === "destructive",
          },
          {
            "h-10 px-4 py-2": size === "default",
            "h-8 px-3 text-xs": size === "sm",
            "h-12 px-8": size === "lg",
            "h-10 w-10": size === "icon",
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
