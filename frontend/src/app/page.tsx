export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-4">
          Welcome to FinRack
        </h1>
        <p className="text-center text-muted-foreground mb-8">
          AI-Powered Financial Platform with Multi-Agent System
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">🤖 7 AI Agents</h2>
            <p className="text-sm text-muted-foreground">
              Autonomous agents for budgeting, fraud detection, investments, and more
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">🏦 Bank Integration</h2>
            <p className="text-sm text-muted-foreground">
              Connect 11,000+ banks via Plaid for automatic transaction sync
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">📊 Smart Analytics</h2>
            <p className="text-sm text-muted-foreground">
              Real-time insights and forecasting powered by machine learning
            </p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-xl font-semibold mb-2">🔒 Secure & Private</h2>
            <p className="text-sm text-muted-foreground">
              Bank-level encryption with optional local AI processing
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
