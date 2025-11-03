'use client'

import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { useState } from 'react'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
})

type FormValues = z.infer<typeof schema>

export default function LoginPage() {
  const { login } = useAuth()
  const [submitting, setSubmitting] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormValues) => {
    setSubmitting(true)
    try {
      await login(data.email, data.password)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">Email</label>
        <input className="w-full rounded-md border px-3 py-2 text-sm" placeholder="you@example.com" {...register('email')} />
        {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Password</label>
        <input type="password" className="w-full rounded-md border px-3 py-2 text-sm" placeholder="••••••••" {...register('password')} />
        {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
      </div>
      <button disabled={submitting} className="w-full rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm disabled:opacity-50">
        {submitting ? 'Signing in...' : 'Sign in'}
      </button>
      <div className="flex justify-between text-xs text-muted-foreground">
        <Link href="/register" className="hover:underline">Create account</Link>
        <Link href="/forgot-password" className="hover:underline">Forgot password?</Link>
      </div>
    </form>
  )
}


