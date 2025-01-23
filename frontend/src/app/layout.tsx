// src/app/layout.tsx
import { Inter } from "next/font/google"
import "./globals.css"
import Navbar from "@/components/common/Navbar"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "Aether AI - Advanced AI Solutions",
  description: "AI products that put innovation at the frontier",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-[#fdf8f6]`}>
        <Navbar />
        {children}
      </body>
    </html>
  )
}