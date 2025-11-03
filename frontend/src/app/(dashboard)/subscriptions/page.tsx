'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'

type Sub = { merchant: string; count: number; avg_monthly_cost: number }

export default function SubscriptionsPage() {
  const [subs, setSubs] = useState<Sub[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/api/subscriptions')
        setSubs(res.data || [])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-4">
      <div className="text-xl font-semibold">Subscriptions</div>
      <div className="rounded-lg border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-3 py-2">Merchant</th>
              <th className="text-left px-3 py-2">Occurrences</th>
              <th className="text-left px-3 py-2">Avg Monthly Cost</th>
            </tr>
          </thead>
          <tbody>
            {subs.map(s => (
              <tr key={s.merchant} className="border-t">
                <td className="px-3 py-2">{s.merchant}</td>
                <td className="px-3 py-2">{s.count}</td>
                <td className="px-3 py-2">${s.avg_monthly_cost.toFixed(2)}</td>
              </tr>
            ))}
            {subs.length === 0 && (
              <tr>
                <td colSpan={3} className="px-3 py-6 text-center text-muted-foreground">
                  {loading ? 'Loading…' : 'No recurring subscriptions detected'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}


