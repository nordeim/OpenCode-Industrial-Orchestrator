/**
 * NEW TRAINING JOB PAGE
 */

"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useCreateFineTuningJob } from "@/lib/api/fine-tuning"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { ArrowLeft, Cpu, Settings2 } from "lucide-react"
import Link from "next/link"

export default function NewFineTuningJobPage() {
  const router = useRouter()
  const createMutation = useCreateFineTuningJob()
  
  const [formData, setFormData] = useState({
    base_model: "mistralai/Mistral-7B-v0.1",
    target_model_name: "INDUSTRIAL-EXPERT-",
    epochs: 3,
    learning_rate: 0.00005
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const job = await createMutation.mutateAsync(formData)
      router.push(`/fine-tuning/${job.id}`)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <Link href="/fine-tuning" className="flex items-center gap-2 text-xs font-mono text-muted-foreground hover:text-accent mb-6 uppercase">
        <ArrowLeft className="h-3 w-3" /> Back to Registry
      </Link>

      <header className="mb-8">
        <h1 className="text-2xl font-bold font-mono tracking-tight uppercase mb-2">INITIATE TRAINING PIPELINE</h1>
        <p className="text-muted-foreground text-sm font-mono uppercase">Configure parameters for model specialization</p>
      </header>

      <Card className="p-6 border-2 border-border brutal-shadow-lg">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-bold font-mono uppercase text-muted-foreground">Base Model Identifier</label>
            <Input 
              value={formData.base_model}
              onChange={e => setFormData({...formData, base_model: e.target.value})}
              placeholder="e.g. meta-llama/Llama-2-7b-hf"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold font-mono uppercase text-muted-foreground">Target Model Name</label>
            <Input 
              value={formData.target_model_name}
              onChange={e => setFormData({...formData, target_model_name: e.target.value.toUpperCase()})}
              placeholder="INDUSTRIAL-CODER-V2"
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-bold font-mono uppercase text-muted-foreground">Epochs</label>
              <Input 
                type="number"
                value={formData.epochs}
                onChange={e => setFormData({...formData, epochs: parseInt(e.target.value)})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold font-mono uppercase text-muted-foreground">Learning Rate</label>
              <Input 
                type="number"
                step="0.00001"
                value={formData.learning_rate}
                onChange={e => setFormData({...formData, learning_rate: parseFloat(e.target.value)})}
              />
            </div>
          </div>

          <div className="p-4 bg-muted/50 border-2 border-dashed border-border">
            <div className="flex items-center gap-2 mb-2">
              <Settings2 className="h-3 w-3 text-accent" />
              <span className="text-[10px] font-bold font-mono uppercase">Hyperparameter Lock</span>
            </div>
            <p className="text-[9px] text-muted-foreground font-mono uppercase leading-relaxed">
              PEFT (LoRA) will be applied by default with Rank 8. Higher precision training requires external GPU cluster allocation.
            </p>
          </div>

          <Button 
            type="submit" 
            variant="accent" 
            className="w-full"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? "PROVISIONING..." : "CREATE TRAINING JOB"}
          </Button>
        </form>
      </Card>
    </div>
  )
}
