import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import './globals.css';

import { AuthProvider } from '@/lib/auth';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Kirobi Portal',
  description: 'Dein persönlicher KI-Begleiter',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="de" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} aurora-bg min-h-screen bg-void text-white`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
