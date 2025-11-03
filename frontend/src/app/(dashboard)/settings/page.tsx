'use client'

import { useState } from 'react'
import { usePlaidLink } from 'react-plaid-link'
import api from '@/lib/api'

const tabs = ['profile', 'accounts', 'notifications', 'security', 'preferences', 'privacy'] as const
type Tab = typeof tabs[number]

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('profile')
  const [linkToken, setLinkToken] = useState<string | null>(null)

  const onSuccess = async (public_token: string) => {
    await api.post('/api/plaid/exchange', { public_token })
    alert('Bank account linked!')
  }

  const { open, ready } = usePlaidLink({ token: linkToken || '', onSuccess })

  const createLinkToken = async () => {
    const res = await api.post('/api/plaid/create-link-token')
    setLinkToken(res.data.link_token)
  }

  return (
    <div className="space-y-4">
      <div className="text-xl font-semibold">Settings</div>
      <div className="flex flex-wrap gap-2">
        {tabs.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md border px-3 py-1.5 text-sm capitalize ${tab === t ? 'bg-accent' : ''}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'profile' && (
        <div className="rounded-lg border p-4 space-y-3">
          <div className="text-sm font-medium">Profile</div>
          <div className="grid gap-3 md:grid-cols-2">
            <input className="rounded-md border px-3 py-2 text-sm" placeholder="Full name" />
            <input className="rounded-md border px-3 py-2 text-sm" placeholder="Email" />
          </div>
          <button className="rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm">Save changes</button>
        </div>
      )}

      {tab === 'accounts' && (
        <div className="rounded-lg border p-4 space-y-3">
          <div className="text-sm font-medium">Bank Accounts</div>
          <div className="text-sm text-muted-foreground">Link accounts using Plaid Link.</div>
          {!linkToken ? (
            <button onClick={createLinkToken} className="rounded-md border px-3 py-2 text-sm">Get Link Token</button>
          ) : (
            <button onClick={() => open()} disabled={!ready} className="rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm disabled:opacity-50">Open Plaid Link</button>
          )}
        </div>
      )}

      {tab === 'notifications' && (
        <div className="rounded-lg border p-4 space-y-3">
          <div className="text-sm font-medium">Notifications</div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4" /> Email alerts for large transactions
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4" /> Weekly spending summary
          </label>
        </div>
      )}

      {tab === 'security' && (
        <div className="rounded-lg border p-4 space-y-3">
          <div className="text-sm font-medium">Security</div>
          <button className="rounded-md border px-3 py-2 text-sm">Enable 2FA</button>
        </div>
      )}

      {tab === 'preferences' && (
        <div className="rounded-lg border p-4 space-y-3">
          <div className="text-sm font-medium">Preferences</div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4" /> Dark mode
          </label>
          <div className="grid gap-2 md:max-w-xs">
            <label className="text-sm">Base currency</label>
            <select className="rounded-md border px-3 py-2 text-sm">
              <option>USD</option>
              <option>EUR</option>
              <option>INR</option>
            </select>
          </div>
        </div>
      )}

      {tab === 'privacy' && (
        <div className="rounded-lg border p-4 space-y-3">
          <div className="text-sm font-medium">Privacy</div>
          <p className="text-sm text-muted-foreground">Manage data retention and sharing preferences.</p>
          <button className="rounded-md border px-3 py-2 text-sm">Export data</button>
        </div>
      )}
    </div>
  )
}


