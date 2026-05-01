import type { ReactNode } from "react"
import { Database, FileText, GitCompareArrows, SearchCheck, Workflow } from "lucide-react"

import { workflowSteps } from "@/lib/docusage"

function ModuleCard({ icon, title, description }: { icon: ReactNode; title: string; description: string }) {
  return (
    <div className="rounded-[24px] border border-purple-200/50 bg-gradient-to-br from-purple-50 to-indigo-50/30 p-5 shadow-sm">
      <div className="inline-flex rounded-2xl border border-purple-200 bg-white p-3 text-purple-700 shadow-sm">{icon}</div>
      <h3 className="mt-4 text-lg font-semibold text-slate-950">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </div>
  )
}

export default function WorkflowPage() {
  return (
    <div className="min-h-[calc(100vh-5rem)] bg-gradient-to-br from-purple-50/50 via-transparent to-indigo-50/30">
      <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8 lg:py-16">
        <div className="rounded-[36px] border border-slate-200 bg-white/80 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] sm:p-10 backdrop-blur-[18px]">
          <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-purple-200 bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700 shadow-sm">
            <Workflow className="size-4" />
            Pipeline anatomy
          </div>
          <h1 className="mt-6 font-serif text-5xl tracking-tight text-slate-950 sm:text-6xl">
            How DocuSage moves from PDF to answer.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
            This page maps the backend implementation directly to the end-user experience so the product is easy to
            explain, debug, and extend.
          </p>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-4">
          {workflowSteps.map((step) => (
            <div key={step.step} className="rounded-[24px] border border-purple-200/50 bg-gradient-to-br from-purple-50/50 to-indigo-50/30 p-5 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-[0.28em] text-purple-700">{step.step}</p>
              <h3 className="mt-3 text-xl font-semibold text-slate-950">{step.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{step.description}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-4 xl:grid-cols-4">
          <ModuleCard
            icon={<FileText className="size-5" />}
            title="pdf_parser.py"
            description="Extracts structure-rich text from PDFs, preserving tables and formatting cues that matter for retrieval."
          />
          <ModuleCard
            icon={<GitCompareArrows className="size-5" />}
            title="chunker_reworked.py"
            description="Builds hierarchical chunks so the model sees coherent sections instead of arbitrary token windows."
          />
          <ModuleCard
            icon={<Database className="size-5" />}
            title="runner.py"
            description="Embeds, stores, searches, reranks, prompts the LLM, and cleans up request-specific vectors."
          />
          <ModuleCard
            icon={<SearchCheck className="size-5" />}
            title="app.py"
            description="Acts as the API layer that accepts uploads or URLs and orchestrates the whole workflow in one call."
          />
        </div>
        </div>
      </div>
    </div>
  )
}
