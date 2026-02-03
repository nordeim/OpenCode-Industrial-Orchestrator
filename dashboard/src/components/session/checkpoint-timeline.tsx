import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

// Temporary interface until added to global types
interface Checkpoint {
  id: string
  sequence: number
  created_at: string
  trigger: string
  state_hash?: string
}

interface CheckpointTimelineProps {
  checkpoints?: Checkpoint[]
}

export function CheckpointTimeline({ checkpoints = [] }: CheckpointTimelineProps) {
  if (!checkpoints || checkpoints.length === 0) {
    return (
      <Card title="CHECKPOINTS" className="h-full min-h-[200px] flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground text-xs mb-2">NO CHECKPOINTS</p>
          <p className="text-[10px] text-muted-foreground/50 max-w-[150px] mx-auto">
            Session has not generated any recovery points yet.
          </p>
        </div>
      </Card>
    )
  }

  // Sort by sequence desc (newest first)
  const sortedCheckpoints = [...checkpoints].sort((a, b) => b.sequence - a.sequence)

  return (
    <Card title="RECOVERY POINTS" className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto space-y-4 p-2">
        {sortedCheckpoints.map((cp, idx) => (
          <div key={cp.id} className="relative pl-4 border-l-2 border-border last:border-0 pb-4">
            {/* Timeline dot */}
            <div className="absolute -left-[5px] top-1 w-2 h-2 bg-accent rounded-none rotate-45" />
            
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold font-mono">
                  SEQ #{cp.sequence.toString().padStart(3, '0')}
                </span>
                <span className="text-[10px] text-muted-foreground tabular-nums">
                  {new Date(cp.created_at).toLocaleTimeString()}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[10px] py-0 h-4">
                  {cp.trigger}
                </Badge>
                {idx === 0 && (
                  <Badge variant="success" className="text-[10px] py-0 h-4">
                    LATEST
                  </Badge>
                )}
              </div>
              
              {cp.state_hash && (
                <div className="text-[10px] font-mono text-muted-foreground truncate mt-1">
                  HASH: {cp.state_hash.substring(0, 12)}...
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="pt-2 mt-auto border-t border-border/50">
         <div className="flex justify-between items-center text-[10px] text-muted-foreground uppercase">
           <span>Total Points</span>
           <span className="font-mono font-bold text-foreground">{checkpoints.length}</span>
         </div>
      </div>
    </Card>
  )
}
