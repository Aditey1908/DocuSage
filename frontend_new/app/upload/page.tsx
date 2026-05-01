import { ArrowRight, UploadCloud } from "lucide-react"

import DocQAWidget from "@/components/doc-qa-widget"

function UploadSidebarCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[24px] border border-blue-200/50 bg-gradient-to-br from-blue-50 to-cyan-50/30 p-5 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-700">{title}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
    </div>
  )
}

export default function UploadPage() {
  return (
    <div className="min-h-[calc(100vh-5rem)] bg-gradient-to-br from-blue-50/50 via-transparent to-cyan-50/30">
      <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8 lg:py-16">
        <div className="rounded-[36px] border border-slate-200 bg-white/80 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] sm:p-10 backdrop-blur-[18px]">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 shadow-sm">
            <UploadCloud className="size-4" />
            Document ingestion
          </div>
          <h1 className="mt-6 font-serif text-5xl leading-tight tracking-tight text-slate-950 sm:text-6xl">
            Upload a PDF and ask anything about it.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
            This is the working DocuSage entry point. It forwards your document to the Flask backend, which extracts,
            chunks, embeds, reranks, and answers before returning structured JSON.
          </p>
        </div>

        <div className="mt-10 flex flex-col gap-8 xl:flex-row">
          <div className="grid gap-4 xl:w-80 xl:flex-shrink-0">
            <UploadSidebarCard
              title="Tip"
              description="Direct file upload is more reliable than hosted URLs for local testing."
            />
            <UploadSidebarCard
              title="What happens next"
              description="The backend stores request-scoped chunks in Astra DB, answers questions in parallel, and cleans up automatically."
            />
            <div className="rounded-[24px] bg-gradient-to-br from-blue-950 to-cyan-950 p-5 text-white shadow-[0_20px_60px_rgba(15,23,42,0.18)]">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-300">Flow</p>
              <div className="mt-4 flex items-center gap-3 text-sm text-blue-100">
                <ArrowRight className="size-4 text-blue-300" />
                POST /process
              </div>
              <div className="mt-2 flex items-center gap-3 text-sm text-blue-100">
                <ArrowRight className="size-4 text-blue-300" />
                parse + chunk + embed
              </div>
              <div className="mt-2 flex items-center gap-3 text-sm text-blue-100">
                <ArrowRight className="size-4 text-blue-300" />
                rerank + answer + cleanup
              </div>
            </div>
          </div>

          <div className="flex-1">
            <DocQAWidget />
          </div>
        </div>
        </div>
      </div>
    </div>
  )
}
