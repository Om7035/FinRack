'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts'

type Transaction = {
  id: string
  date: string
  merchant: string
  amount: number
  category: string
}

export default function DashboardPage() {
  const [recent, setRecent] = useState<Transaction[]>([])
  const [trend, setTrend] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const [r1, r2, r3] = await Promise.all([
          api.get('/api/transactions?limit=5'),
          api.get('/api/analytics/spending-trend'),
          api.get('/api/analytics/category-breakdown'),
        ])
        setRecent(r1.data || [])
        setTrend(r2.data || [])
        setCategories(r3.data || [])
      } catch {
        // noop fallback UI
      }
    }
    load()
  }, [])

  const COLORS = ['#4f46e5', '#22c55e', '#f97316', '#e11d48', '#06b6d4']

  return (
    <div className="space-y-6">
      {/* Overview cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[{ label: 'Balance', value: '$24,320' }, { label: 'Income (30d)', value: '$8,200' }, { label: 'Expenses (30d)', value: '$5,780' }, { label: 'Savings Rate', value: '29%' }].map(card => (
          <div key={card.label} className="rounded-lg border p-4">
            <div className="text-sm text-muted-foreground">{card.label}</div>
            <div className="mt-2 text-2xl font-semibold">{card.value}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border p-4">
          <div className="mb-3 text-sm font-medium">Spending Trend</div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <XAxis dataKey="date" hide />
                <YAxis hide />
                <Tooltip />
                <Line type="monotone" dataKey="amount" stroke="#4f46e5" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-lg border p-4">
          <div className="mb-3 text-sm font-medium">Category Breakdown</div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={categories} dataKey="value" nameKey="name" outerRadius={100}>
                  {categories.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent transactions */}
      <div className="rounded-lg border">
        <div className="border-b p-4 text-sm font-medium">Recent Transactions</div>
        <div className="divide-y">
          {recent.map(tx => (
            <div key={tx.id} className="flex items-center justify-between p-4 text-sm">
              <div className="flex items-center gap-3">
                <div className="font-medium">{tx.merchant}</div>
                <div className="text-muted-foreground">{tx.category}</div>
              </div>
              <div className={tx.amount < 0 ? 'text-red-500' : 'text-green-600'}>
                {tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount).toFixed(2)}
              </div>
            </div>
          ))}
          {recent.length === 0 && (
            <div className="p-6 text-center text-sm text-muted-foreground">No recent transactions</div>
          )}
        </div>
      </div>
    </div>
  )
}


