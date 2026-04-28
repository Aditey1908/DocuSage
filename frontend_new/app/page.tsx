import Link from "next/link"
import { ArrowRight, BrainCircuit, Database, FileSearch, Layers3, Sparkles, UploadCloud, WandSparkles } from "lucide-react"

import DocQAWidget from "@/components/doc-qa-widget"
import { Button } from "@/components/ui/button"
import { productHighlights, workflowSteps } from "@/lib/docusage"

import type { ReactNode } from "react"

function SectionHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="max-w-3xl space-y-4">
      <p className="text-sm font-semibold uppercase tracking-[0.28em] text-emerald-700">{eyebrow}</p>
      <h2 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">{title}</h2>
      <p className="text-base leading-7 text-slate-600">{description}</p>
    </div>
  )
}

function HighlightCard({ icon, title, description }: { icon: ReactNode; title: string; description: string }) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white/80 p-5 shadow-sm">
      <div className="mb-4 inline-flex rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-emerald-700 shadow-sm">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-slate-950">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </div>
  )
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-[24px] border border-emerald-200/50 bg-gradient-to-br from-emerald-50 to-teal-50/30 p-5 shadow-sm">
      <p className="font-serif text-3xl text-emerald-900">{value}</p>
      <p className="mt-1 text-sm text-slate-600">{label}</p>
    </div>
  )
}

export default function HomePage() {
  const featureIcons = [
    <FileSearch key="search" className="size-5" />,
    <Layers3 key="layers" className="size-5" />,
    <Database key="database" className="size-5" />,
    <BrainCircuit key="brain" className="size-5" />,
  ]

  return (
    <div className="space-y-24 pb-24 bg-gradient-to-br from-emerald-50/40 via-transparent to-teal-50/20">
      <section className="px-4 pt-10 sm:pt-14 lg:px-8 lg:pt-16">
        <div className="mx-auto max-w-7xl">
          <div className="relative overflow-hidden rounded-[36px] border border-slate-200 bg-white/80 px-6 py-10 shadow-[0_24px_80px_rgba(15,23,42,0.08)] sm:px-10 sm:py-14 lg:px-16 lg:py-20 backdrop-blur-[18px]">
            <div className="absolute -right-20 top-10 h-72 w-72 rounded-full bg-emerald-400/20 blur-3xl" />
            <div className="absolute -left-16 bottom-0 h-64 w-64 rounded-full bg-slate-900/10 blur-3xl" />

            <div className="relative max-w-3xl space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 shadow-sm">
                <Sparkles className="size-4" />
                Built for dense PDFs, policies, and technical documents
              </div>

              <h1 className="max-w-4xl font-serif text-5xl leading-[1.02] tracking-tight text-slate-950 sm:text-6xl lg:text-7xl">
                Turn documents into answers, not just text.
              </h1>

              <p className="max-w-2xl text-lg leading-8 text-slate-600">
                DocuSage parses PDFs, chunks them with structure-aware logic, stores embeddings in Astra DB, reranks
                the best matches, and returns concise answers with cleanup built in.
              </p>

              <div className="flex flex-wrap gap-3">
                <Button asChild className="rounded-full bg-emerald-600 px-6 text-white hover:bg-emerald-700">
                  <Link href="/upload">
                    Upload a PDF <ArrowRight className="ml-2 size-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" className="rounded-full border-slate-200 bg-white/90 px-6 text-slate-700 hover:bg-slate-50">
                  <Link href="/workflow">See the workflow</Link>
                </Button>
              </div>
            </div>

            <div className="relative mt-12 grid gap-4 md:grid-cols-3">
              <StatCard value="PDF → chunks" label="Structure-aware parsing and chunking" />
              <StatCard value="Astra DB" label="Vector storage with request-scoped cleanup" />
              <StatCard value="OpenAI + VoyageAI" label="Embedding, reranking, and answer generation" />
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 lg:px-8">
        <SectionHeader
          eyebrow="Why DocuSage"
          title="A product surface that matches the pipeline underneath"
          description="This frontend is wired to the same backend flow the README describes, so users can inspect the process, run a document, and understand the architecture without leaving the app."
        />

        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {productHighlights.map((item, index) => (
            <HighlightCard
              key={item.title}
              icon={featureIcons[index]}
              title={item.title}
              description={item.description}
            />
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 lg:px-8">
        <SectionHeader
          eyebrow="Workflow"
          title="One pass from upload to answer"
          description="The frontend explains the same four-stage flow used by the Python backend so the app feels coherent end to end."
        />

        <div className="mt-8 grid gap-4 lg:grid-cols-4">
          {workflowSteps.map((step) => (
            <div key={step.step} className="rounded-[24px] border border-emerald-200/50 bg-gradient-to-br from-emerald-50/50 to-teal-50/30 p-5 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-[0.28em] text-emerald-700">{step.step}</p>
              <h3 className="mt-3 text-xl font-semibold text-slate-950">{step.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{step.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-[1fr_1fr]">
          <div className="space-y-6">
            <SectionHeader
              eyebrow="Live demo"
              title="Run DocuSage on a real document"
              description="Paste a PDF URL or upload a local file. The frontend sends the payload to the Flask API and renders the answer back as a clean, readable view."
            />
            <div className="rounded-[28px] border border-slate-200 bg-white/80 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl bg-gradient-to-br from-emerald-900 to-teal-900 px-4 py-4 text-white">
                  <UploadCloud className="size-5 text-emerald-300" />
                  <p className="mt-3 text-sm font-semibold">Upload</p>
                  <p className="mt-1 text-xs leading-5 text-emerald-200">PDF file or URL</p>
                </div>
                <div className="rounded-2xl bg-slate-100 px-4 py-4 text-slate-900">
                  <WandSparkles className="size-5 text-emerald-700" />
                  <p className="mt-3 text-sm font-semibold">Process</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">Parse, chunk, embed, rerank</p>
                </div>
                <div className="rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 px-4 py-4 text-slate-900">
                  <ArrowRight className="size-5 text-emerald-700" />
                  <p className="mt-3 text-sm font-semibold">Answer</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">Clean response</p>
                </div>
              </div>
            </div>
          </div>

          <DocQAWidget />
        </div>
      </section>
    </div>
  )
}
