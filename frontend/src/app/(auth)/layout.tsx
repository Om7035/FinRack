export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen grid place-items-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="text-2xl font-bold">FinRack</div>
          <p className="text-sm text-muted-foreground">Sign in to continue</p>
        </div>
        <div className="rounded-lg border p-6 bg-background shadow-sm">
          {children}
        </div>
      </div>
    </div>
  )
}


