'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

type Goal = { id: string; name: string; target: number; saved: number; targetDate?: string };

export default function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/api/goals')
        setGoals(res.data || [])
      } catch {
        setGoals([])
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xl font-semibold">Goals</div>
        <button className="rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm">Create Goal</button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {goals.map(g => {
          const pct = Math.min(100, Math.round((g.saved / g.target) * 100))
          return (
            <div key={g.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="font-medium">{g.name}</div>
                <div className="text-xs text-muted-foreground">Target: ${g.target.toFixed(2)}</div>
              </div>
              <div className="text-sm text-muted-foreground">Saved: ${g.saved.toFixed(2)} ({pct}%)</div>
              <div className="h-2 w-full rounded bg-muted">
                <div className="h-2 rounded bg-green-600" style={{ width: pct + '%' }} />
              </div>
              {g.targetDate && (
                <div className="text-xs text-muted-foreground">By {new Date(g.targetDate).toLocaleDateString()}</div>
              )}
              <button className="text-sm underline">View details</button>
            </div>
          )
        })}
        {goals.length === 0 && (
          <div className="col-span-full text-center text-sm text-muted-foreground">No goals yet</div>
        )}
      </div>

      <div className="rounded-lg border p-4">
        <div className="mb-2 text-sm font-medium">Projections</div>
        <p className="text-sm text-muted-foreground">Estimated timeline and required monthly savings based on your cash flow.</p>
      </div>
    </div>
  )
}


