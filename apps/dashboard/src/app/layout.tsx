import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { DashboardShell } from '@/components/dashboard-shell'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'Kirobi Dashboard',
    template: '%s · Kirobi Admin',
  },
  description: 'Admin-Dashboard für das OpenDisruption-Ökosystem — Service-Status, Analytics und System-Übersicht.',
  robots: 'noindex, nofollow',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de" className="dark">
      <body className={`${inter.className} relative`}>
        <div className="ambient-field" aria-hidden="true" />
        <DashboardShell>{children}</DashboardShell>
      </body>
    </html>
  )
}
