'use client'

import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import Link from 'next/link'
import api from '@/lib/api'
import { useState } from 'react'

const schema = z.object({
  email: z.string().email(),
})

type FormValues = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormValues) => {
    setSubmitting(true)
    try {
      await api.post('/api/auth/forgot-password', { email: data.email })
      setSent(true)
    } finally {
      setSubmitting(false)
    }
  }

  if (sent) {
    return (
      <div className="space-y-3 text-center">
        <div className="text-lg font-semibold">Check your email</div>
        <p className="text-sm text-muted-foreground">We sent a password reset link if an account exists for that email.</p>
        <Link href="/login" className="text-sm underline">Back to sign in</Link>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">Email</label>
        <input className="w-full rounded-md border px-3 py-2 text-sm" placeholder="you@example.com" {...register('email')} />
        {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
      </div>
      <button disabled={submitting} className="w-full rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm disabled:opacity-50">
        {submitting ? 'Sending...' : 'Send reset link'}
      </button>
      <div className="text-center text-xs">
        <Link href="/login" className="text-muted-foreground hover:underline">Back to sign in</Link>
      </div>
    </form>
  )
}


