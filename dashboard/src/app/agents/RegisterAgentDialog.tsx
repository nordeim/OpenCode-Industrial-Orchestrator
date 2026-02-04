"use client"

import { useState } from "react"
import { Dialog } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useRegisterExternalAgent } from "@/lib/api/agents"
import type { EAPRegistrationRequest } from "@/lib/api/types"

interface RegisterAgentDialogProps {
  isOpen: boolean
  onClose: () => void
}

export function RegisterAgentDialog({ isOpen, onClose }: RegisterAgentDialogProps) {
  const registerMutation = useRegisterExternalAgent()
  const [formData, setFormData] = useState<EAPRegistrationRequest>({
    protocol_version: "1.0",
    name: "AGENT-EXT-",
    version: "1.0.0",
    agent_type: "IMPLEMENTER",
    capabilities: ["CODE_GENERATION"],
    endpoint_url: "",
    metadata: {}
  })

  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{ id: string; token: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    try {
      const response = await registerMutation.mutateAsync(formData)
      setResult({ id: response.agent_id, token: response.auth_token })
    } catch (err: any) {
      setError(err.message || "Registration failed")
    }
  }

  const handleClose = () => {
    setResult(null)
    setError(null)
    onClose()
  }

  if (result) {
    return (
      <Dialog 
        isOpen={isOpen} 
        onClose={handleClose} 
        title="REGISTRATION SUCCESSFUL"
        description="Save these credentials. The token will not be shown again."
      >
        <div className="space-y-4">
          <div className="p-4 bg-status-running/10 border-2 border-status-running/50 text-status-running space-y-2">
            <div>
              <span className="text-[10px] uppercase font-bold opacity-70 block">Agent ID</span>
              <code className="text-sm break-all">{result.id}</code>
            </div>
            <div>
              <span className="text-[10px] uppercase font-bold opacity-70 block">Auth Token (X-Agent-Token)</span>
              <code className="text-sm break-all">{result.token}</code>
            </div>
          </div>
          <Button onClick={handleClose} className="w-full">ACKNOWLEDGE & CLOSE</Button>
        </div>
      </Dialog>
    )
  }

  return (
    <Dialog 
      isOpen={isOpen} 
      onClose={onClose} 
      title="REGISTER EXTERNAL AGENT"
      description="Connect an autonomous agent speaking the EAP v1.0 protocol."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Agent Name</label>
          <Input 
            required
            value={formData.name}
            onChange={e => setFormData({...formData, name: e.target.value.toUpperCase()})}
            placeholder="AGENT-EXT-CUSTOM"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Endpoint URL (Webhook)</label>
          <Input 
            value={formData.endpoint_url}
            onChange={e => setFormData({...formData, endpoint_url: e.target.value})}
            placeholder="http://agent-service:8080"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</label>
            <select 
              className="w-full h-10 border-2 border-border bg-card px-3 py-2 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-ring"
              value={formData.agent_type}
              onChange={e => setFormData({...formData, agent_type: e.target.value})}
            >
              <option value="ARCHITECT">Architect</option>
              <option value="IMPLEMENTER">Implementer</option>
              <option value="REVIEWER">Reviewer</option>
              <option value="DEBUGGER">Debugger</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Version</label>
            <Input 
              value={formData.version}
              onChange={e => setFormData({...formData, version: e.target.value})}
            />
          </div>
        </div>

        {error && (
          <div className="p-3 bg-status-failed/10 border-2 border-status-failed text-status-failed text-xs">
            ERROR: {error}
          </div>
        )}

        <div className="pt-4 flex gap-3">
          <Button type="button" variant="outline" onClick={onClose} className="flex-1">CANCEL</Button>
          <Button type="submit" variant="accent" className="flex-1" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? "REGISTERING..." : "REGISTER AGENT"}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
