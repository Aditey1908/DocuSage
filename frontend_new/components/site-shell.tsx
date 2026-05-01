import Link from "next/link"
import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"
import PageBackground from "@/components/page-background"
import { navLinks } from "@/lib/docusage"

function BrandMark() {
  return (
    <img
      src="/docusage-logo.png"
      alt="DocuSage Logo"
      className="h-14 w-14 rounded-2xl border border-slate-200 bg-white object-contain p-1.5 shadow-sm sm:h-16 sm:w-16"
    />
  )
}

export function SiteShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen text-slate-900">
      <header className="sticky top-0 z-50 border-b border-white/60 bg-white/75 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <BrandMark />
            <div>
              <p className="font-serif text-xl tracking-tight text-slate-950">DocuSage</p>
              <p className="text-xs text-slate-500">RAG pipeline for complex documents</p>
            </div>
          </Link>

          <nav className="hidden items-center gap-1 rounded-full border border-slate-200 bg-white/80 px-2 py-1 shadow-sm lg:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-full px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-950 hover:text-white"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <Button asChild variant="outline" className="hidden rounded-full border-slate-200 bg-white/80 text-slate-700 sm:inline-flex">
              <Link href="/workflow">See workflow</Link>
            </Button>
            <Button asChild className="rounded-full bg-slate-950 px-5 text-white hover:bg-slate-800">
              <Link href="/upload">Try it now</Link>
            </Button>
          </div>
        </div>
      </header>

      <main>
        <PageBackground className="min-h-[calc(100vh-5rem)]">{children}</PageBackground>
      </main>

      <footer className="border-t border-slate-200/80 bg-white/70">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[1.4fr_1fr_1fr] lg:px-8">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <BrandMark />
              <div>
                <p className="font-serif text-xl text-slate-950">DocuSage</p>
                <p className="text-sm text-slate-500">Parse, chunk, embed, search, answer.</p>
              </div>
            </div>
            <p className="max-w-md text-sm leading-6 text-slate-600">
              Built for dense policy documents, reports, and contracts that need structure-aware retrieval instead of
              generic OCR output.
            </p>
          </div>

          <div>
            <p className="mb-3 text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Navigate</p>
            <div className="grid gap-2 text-sm text-slate-600">
              {navLinks.map((link) => (
                <Link key={link.href} href={link.href} className="transition hover:text-slate-950">
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-3 text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Backend</p>
            <div className="grid gap-2 text-sm text-slate-600">
              <span>Flask API at localhost:5000</span>
              <span>Next.js frontend at localhost:3000</span>
              <span>Run both with start_all.ps1</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
