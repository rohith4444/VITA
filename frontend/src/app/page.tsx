// src/app/page.tsx
import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <main className="container mx-auto px-4 py-24">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="text-6xl font-bold leading-tight mb-16">
            AI <span className="underline decoration-2">products</span> that put innovation at the frontier
          </h1>

          <div className="grid gap-6">
            {/* VITA Card */}
            <div className="bg-white rounded-xl p-8 shadow-sm">
              <div className="text-sm font-medium text-neutral-600 mb-4">VITA.AI</div>
              <h2 className="text-2xl font-semibold mb-2">Meet VITA Assistant</h2>
              <p className="text-neutral-600 mb-6">
                VITA, our most advanced AI model, is now available.
              </p>
              <Button 
                variant="default"
                className="w-full bg-black text-white hover:bg-neutral-800"
              >
                Talk to VITA
              </Button>
            </div>

            {/* API Card */}
            <div className="bg-white rounded-xl p-8 shadow-sm">
              <div className="text-sm font-medium text-neutral-600 mb-4">API</div>
              <h2 className="text-2xl font-semibold mb-2">Build with VITA</h2>
              <p className="text-neutral-600 mb-6">
                Create AI-powered applications and custom experiences using VITA.
              </p>
              <Button 
                variant="outline" 
                className="w-full"
              >
                Learn more
              </Button>
            </div>
          </div>
        </div>

        {/* Decorative Illustration */}
        <div className="hidden lg:block">
          <svg viewBox="0 0 400 400" className="w-full h-auto" style={{ maxWidth: "500px" }}>
            <circle cx="200" cy="200" r="20" fill="#E9967A" />
            <circle cx="300" cy="150" r="20" fill="#E9967A" />
            <circle cx="250" cy="300" r="20" fill="#E9967A" />
            <circle cx="100" cy="250" r="20" fill="#E9967A" />
            <circle cx="150" cy="100" r="20" fill="#E9967A" />
            <path 
              d="M200 200 L300 150 L250 300 L100 250 L150 100 Z" 
              stroke="#E9967A" 
              strokeWidth="2" 
              fill="none" 
            />
            <path 
              d="M280 130 Q310 160 340 140" 
              stroke="black" 
              strokeWidth="4" 
              fill="none" 
            />
          </svg>
        </div>
      </div>
    </main>
  )
}