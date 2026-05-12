import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopBar } from '@/components/layout/TopBar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'KIROBI ADMIN',
    template: '%s · KIROBI ADMIN',
  },
  description: 'Next.js 15 Admin Control UI für OpenDisruption – Services, Modelle, Wissen und lokale Orchestrierung.',
  robots: 'noindex, nofollow',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className="dark">
      <body className={`${inter.className} relative min-h-screen overflow-x-hidden bg-void text-white`}>
        <div className="ambient-field" aria-hidden="true" />
        <div className="relative z-10 flex min-h-screen">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar />
            <main className="flex-1 px-4 pb-6 pt-4 sm:px-6 lg:px-8">{children}</main>
          </div>
        </div>
      </body>
    </html>
  )
}
