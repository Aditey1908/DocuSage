import { CheckCircle2, FileJson2, FolderOpen, PlayCircle } from "lucide-react"

import { envVars } from "@/lib/docusage"

function StepItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-700">{title}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
    </div>
  )
}

export default function DocsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8 lg:py-16">
      <div className="docs-panel rounded-[36px] p-6 sm:p-10">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm">
            <FileJson2 className="size-4 text-emerald-700" />
            Setup and usage
          </div>
          <h1 className="mt-6 font-serif text-5xl tracking-tight text-slate-950 sm:text-6xl">
            Everything needed to run DocuSage locally.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
            These steps match the README and the integrated frontend so the repo is easy to clone, configure, and
            demonstrate without guesswork.
          </p>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
          <StepItem title="1. Install Python deps" description="Run pip install -r requirements_updated.txt from the repo root." />
          <StepItem title="2. Configure env" description="Keep the API keys in DocuSage/.env or your shell environment." />
          <StepItem title="3. Start both apps" description="Use start_all.ps1 to launch Flask and the Next.js frontend together." />
          <StepItem title="4. Test a document" description="Open /upload and submit a PDF URL or local PDF file." />
        </div>

        <div className="mt-10 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-700">Quick commands</p>
            <div className="mt-4 grid gap-3 text-sm text-slate-600">
              <div className="rounded-2xl bg-slate-950 px-4 py-3 font-mono text-xs text-slate-200">
                python DocuSage/app.py
              </div>
              <div className="rounded-2xl bg-slate-950 px-4 py-3 font-mono text-xs text-slate-200">
                cd DocuSage/frontend_new && npm run dev
              </div>
              <div className="rounded-2xl bg-slate-950 px-4 py-3 font-mono text-xs text-slate-200">
                .\\start_all.ps1
              </div>
            </div>
          </div>

          <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-700">Environment variables</p>
            <div className="mt-4 grid gap-2">
              {envVars.map((variable) => (
                <div key={variable} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3 text-sm">
                  <span className="font-mono text-xs text-slate-500">{variable}</span>
                  <CheckCircle2 className="size-4 text-emerald-600" />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
            <FolderOpen className="size-5 text-emerald-700" />
            <h3 className="mt-4 text-lg font-semibold text-slate-950">Where the frontend lives</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">Use the `frontend_new` folder for the current DocuSage UI.</p>
          </div>
          <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
            <PlayCircle className="size-5 text-emerald-700" />
            <h3 className="mt-4 text-lg font-semibold text-slate-950">What the demo does</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">It shows the homepage, upload flow, workflow, API, docs, and results screens.</p>
          </div>
          <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
            <CheckCircle2 className="size-5 text-emerald-700" />
            <h3 className="mt-4 text-lg font-semibold text-slate-950">What success looks like</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">The backend returns a session id, question count, and answer array for each run.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
