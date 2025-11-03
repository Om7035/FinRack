'use client'

import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { useState } from 'react'

const schema = z.object({
  fullName: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(6),
})

type FormValues = z.infer<typeof schema>

export default function RegisterPage() {
  const { register: doRegister } = useAuth()
  const [submitting, setSubmitting] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormValues) => {
    setSubmitting(true)
    try {
      await doRegister(data.email, data.password, data.fullName)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium">Full name</label>
        <input className="w-full rounded-md border px-3 py-2 text-sm" placeholder="Jane Doe" {...register('fullName')} />
        {errors.fullName && <p className="text-xs text-red-500">{errors.fullName.message}</p>}
      </div>
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
        {submitting ? 'Creating account...' : 'Create account'}
      </button>
      <div className="text-center text-xs text-muted-foreground">
        Already have an account? <Link href="/login" className="hover:underline">Sign in</Link>
      </div>
    </form>
  )
}


