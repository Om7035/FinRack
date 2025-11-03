'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

type Budget = { id: string; name: string; limit: number; spent: number };

export default function BudgetsPage() {
  const [budgets, setBudgets] = useState<Budget[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/api/budgets')
        setBudgets(res.data || [])
      } catch {
        setBudgets([])
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xl font-semibold">Budgets</div>
        <button className="rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm">Create Budget</button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {budgets.map(b => {
          const pct = Math.min(100, Math.round((b.spent / b.limit) * 100))
          return (
            <div key={b.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="font-medium">{b.name}</div>
                <button className="text-sm underline">Edit</button>
              </div>
              <div className="text-sm text-muted-foreground">${b.spent.toFixed(2)} / ${b.limit.toFixed(2)}</div>
              <div className="h-2 w-full rounded bg-muted">
                <div className="h-2 rounded bg-primary" style={{ width: pct + '%' }} />
              </div>
            </div>
          )
        })}
        {budgets.length === 0 && (
          <div className="col-span-full text-center text-sm text-muted-foreground">No budgets yet</div>
        )}
      </div>

      <div className="rounded-lg border p-4">
        <div className="mb-2 text-sm font-medium">AI Recommendations</div>
        <p className="text-sm text-muted-foreground">Optimize your categories and limits based on last 90 days of spending.</p>
      </div>
    </div>
  )
}


