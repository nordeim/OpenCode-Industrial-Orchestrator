"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"

interface DialogProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
}

export function Dialog({
  isOpen,
  onClose,
  title,
  description,
  children
}: DialogProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-lg bg-card border-2 border-border brutal-shadow-lg animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b-2 border-border bg-muted/50">
          <div>
            <h2 className="text-lg font-bold tracking-tight font-mono uppercase">{title}</h2>
            {description && (
              <p className="text-sm text-muted-foreground font-mono mt-1">{description}</p>
            )}
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-muted transition-colors border-2 border-transparent hover:border-border"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 font-mono">
          {children}
        </div>
      </div>
    </div>
  )
}
