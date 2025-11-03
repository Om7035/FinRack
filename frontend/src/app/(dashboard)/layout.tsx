'use client'

import { ReactNode, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { Menu, Bell, Search, User } from 'lucide-react'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login')
    }
  }, [loading, user, router])

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  const navItems = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/transactions', label: 'Transactions' },
    { href: '/budgets', label: 'Budgets' },
    { href: '/goals', label: 'Goals' },
    { href: '/ai', label: 'AI Chat' },
    { href: '/settings', label: 'Settings' },
  ]

  const crumbs = pathname
    .split('/')
    .filter(Boolean)
    .map((part, idx, arr) => ({
      label: part[0]?.toUpperCase() + part.slice(1),
      href: '/' + arr.slice(0, idx + 1).join('/'),
    }))

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="grid grid-cols-1 md:grid-cols-[240px_1fr]">
        {/* Sidebar */}
        <aside className="hidden md:block border-r min-h-screen p-4">
          <div className="text-xl font-bold mb-6">FinRack</div>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`block rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground ${
                  pathname === item.href ? 'bg-accent text-accent-foreground' : ''
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>

        {/* Main */}
        <div className="flex flex-col min-h-screen">
          {/* Top bar */}
          <header className="sticky top-0 z-10 flex items-center gap-2 border-b bg-background/80 backdrop-blur p-3">
            <button className="md:hidden rounded-md p-2 hover:bg-accent" aria-label="menu">
              <Menu className="h-5 w-5" />
            </button>
            <div className="relative ml-1 flex-1 max-w-md">
              <input
                placeholder="Search..."
                className="w-full rounded-md border bg-background px-8 py-2 text-sm focus:outline-none"
              />
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
            <button className="rounded-md p-2 hover:bg-accent" aria-label="notifications">
              <Bell className="h-5 w-5" />
            </button>
            <Link href="/settings" className="rounded-md p-2 hover:bg-accent" aria-label="user menu">
              <User className="h-5 w-5" />
            </Link>
          </header>

          {/* Breadcrumbs */}
          <div className="border-b px-4 py-2 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Link href="/dashboard" className="hover:underline">Home</Link>
              {crumbs.map((c, i) => (
                <span key={c.href} className="flex items-center gap-1">
                  <span>/</span>
                  {i === crumbs.length - 1 ? (
                    <span className="text-foreground">{c.label}</span>
                  ) : (
                    <Link href={c.href} className="hover:underline">{c.label}</Link>
                  )}
                </span>
              ))}
            </div>
          </div>

          <main className="flex-1 p-4 md:p-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}


