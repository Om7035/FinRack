'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import api from '@/lib/api'
const ResponsiveContainer = dynamic(() => import('recharts').then(m => m.ResponsiveContainer), { ssr: false }) as any
const LineChart = dynamic(() => import('recharts').then(m => m.LineChart), { ssr: false }) as any
const Line = dynamic(() => import('recharts').then(m => m.Line), { ssr: false }) as any
const XAxis = dynamic(() => import('recharts').then(m => m.XAxis), { ssr: false }) as any
const YAxis = dynamic(() => import('recharts').then(m => m.YAxis), { ssr: false }) as any
const Tooltip = dynamic(() => import('recharts').then(m => m.Tooltip), { ssr: false }) as any
const BarChart = dynamic(() => import('recharts').then(m => m.BarChart), { ssr: false }) as any
const Bar = dynamic(() => import('recharts').then(m => m.Bar), { ssr: false }) as any

export default function AnalyticsPage() {
  const [trend, setTrend] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [forecast, setForecast] = useState<any[]>([])
  const [netWorth, setNetWorth] = useState<any | null>(null)
  const [tax, setTax] = useState<any | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [t, c, f, n, x] = await Promise.all([
          api.get('/api/analytics/spending-trend'),
          api.get('/api/analytics/category-breakdown'),
          api.get('/api/analytics/forecast'),
          api.get('/api/analytics/net-worth'),
          api.get('/api/analytics/tax-estimate'),
        ])
        setTrend(t.data || [])
        setCategories(c.data || [])
        setForecast(f.data || [])
        setNetWorth(n.data || null)
        setTax(x.data || null)
      } catch {
        // silent fail for demo
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4">
          <div className="mb-2 text-sm font-medium">Cash Flow Forecast</div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={forecast}>
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="projected_expenses" fill="#4f46e5" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-lg border p-4">
          <div className="mb-2 text-sm font-medium">Spending Trend</div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <XAxis dataKey="date" hide />
                <YAxis hide />
                <Tooltip />
                <Line type="monotone" dataKey="amount" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-lg border p-4">
        <div className="mb-2 text-sm font-medium">Category Totals (30d)</div>
        <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
          {categories.map((c) => (
            <div key={c.name} className="rounded-md border p-3 text-sm flex items-center justify-between">
              <span className="text-muted-foreground">{c.name}</span>
              <span className="font-medium">${Math.abs(c.value).toFixed(2)}</span>
            </div>
          ))}
          {categories.length === 0 && <div className="text-sm text-muted-foreground">No data</div>}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4 text-sm">
          <div className="mb-2 font-medium">Net Worth</div>
          {netWorth ? (
            <div className="text-2xl font-semibold">${Number(netWorth.net_worth ?? 0).toFixed(2)}</div>
          ) : (
            <div className="text-muted-foreground">No data</div>
          )}
        </div>
        <div className="rounded-lg border p-4 text-sm">
          <div className="mb-2 font-medium">Estimated Tax</div>
          {tax ? (
            <div className="space-y-1">
              <div>Income (YTD): ${Number(tax.year_income ?? 0).toFixed(2)}</div>
              <div>Rate: {(Number(tax.rate) * 100).toFixed(0)}%</div>
              <div className="text-2xl font-semibold">${Number(tax.estimated_tax ?? 0).toFixed(2)}</div>
            </div>
          ) : (
            <div className="text-muted-foreground">No data</div>
          )}
        </div>
      </div>
    </div>
  )
}
