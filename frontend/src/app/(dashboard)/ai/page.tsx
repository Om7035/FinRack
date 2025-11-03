'use client'

import { useEffect, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'

type Message = { id: string; role: 'user' | 'assistant' | 'system'; content: string };

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const socketRef = useRef<Socket | null>(null)

  useEffect(() => {
    const socket = io(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000', { path: '/ws/socket.io' })
    socketRef.current = socket
    socket.on('connect', () => setConnected(true))
    socket.on('disconnect', () => setConnected(false))
    socket.on('ai_response', (payload: any) => {
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: payload.content }])
    })
    return () => { socket.disconnect() }
  }, [])

  const send = () => {
    if (!input.trim()) return
    const msg: Message = { id: crypto.randomUUID(), role: 'user', content: input.trim() }
    setMessages((prev) => [...prev, msg])
    socketRef.current?.emit('ai_message', { content: msg.content })
    setInput('')
  }

  return (
    <div className="flex h-[70vh] flex-col rounded-lg border">
      <div className="flex items-center justify-between border-b px-4 py-2 text-sm">
        <div className="font-medium">AI Chat</div>
        <div className={`flex items-center gap-2 ${connected ? 'text-green-600' : 'text-muted-foreground'}`}>
          <span className={`h-2 w-2 rounded-full ${connected ? 'bg-green-600' : 'bg-muted-foreground'}`} />
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map(m => (
          <div key={m.id} className={`max-w-[80%] rounded-md px-3 py-2 text-sm ${m.role === 'user' ? 'ml-auto bg-primary text-primary-foreground' : 'bg-accent text-accent-foreground'}`}>
            {m.content}
          </div>
        ))}
        {messages.length === 0 && (
          <div className="text-center text-sm text-muted-foreground">Ask about your spending, budgets, or goals…</div>
        )}
      </div>
      <div className="flex items-center gap-2 border-t p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') send() }}
          placeholder="Type your message"
          className="flex-1 rounded-md border px-3 py-2 text-sm"
        />
        <button onClick={send} className="rounded-md bg-primary text-primary-foreground px-3 py-2 text-sm">Send</button>
      </div>
    </div>
  )
}


