import { Code2, Webhook } from "lucide-react"

import { apiRoutes, envVars } from "@/lib/docusage"

function CodeBlock({ title, code }: { title: string; code: string }) {
  return (
    <div className="overflow-hidden rounded-[24px] border border-slate-200 bg-slate-950 shadow-[0_20px_60px_rgba(15,23,42,0.18)]">
      <div className="border-b border-white/10 px-4 py-3 text-sm font-semibold text-white">{title}</div>
      <pre className="overflow-auto p-4 text-xs leading-6 text-slate-200">{code}</pre>
    </div>
  )
}

export default function ApiPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8 lg:py-16">
      <div className="docs-panel rounded-[36px] p-6 sm:p-10">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm">
            <Webhook className="size-4 text-emerald-700" />
            API reference
          </div>
          <h1 className="mt-6 font-serif text-5xl tracking-tight text-slate-950 sm:text-6xl">
            The backend contract used by the frontend.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
            DocuSage ships with a very small API surface so the UI can stay focused on document operations and the
            pipeline can remain easy to reason about.
          </p>
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-2">
          {apiRoutes.map((route) => (
            <div key={route.route} className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-white">
                  {route.method}
                </span>
                <span className="font-mono text-sm text-slate-700">{route.route}</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-600">{route.description}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 grid gap-6 xl:grid-cols-2">
          <CodeBlock
            title="JSON request"
            code={`POST /process
Content-Type: application/json

{
  "documents": "https://example.com/policy.pdf",
  "questions": [
    "What does the document cover?",
    "What are the waiting periods?"
  ]
}`}
          />
          <CodeBlock
            title="Multipart upload"
            code={`POST /process
Content-Type: multipart/form-data

document=<pdf file>
questions=["What is the document about?","Summarize the key limits."]
documents=https://example.com/optional-fallback.pdf`}
          />
        </div>

        <div className="mt-10 grid gap-4 xl:grid-cols-[1fr_1.2fr]">
          <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-700">Environment</p>
            <div className="mt-4 grid gap-2 text-sm text-slate-600">
              {envVars.map((variable) => (
                <div key={variable} className="flex items-center justify-between gap-4 rounded-2xl bg-slate-50 px-4 py-3">
                  <span className="font-mono text-xs text-slate-500">{variable}</span>
                  <span className="text-xs text-slate-400">required</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-700">Response shape</p>
            <CodeBlock
              title="Successful response"
              code={`{
  "session_id": "...",
  "source_type": "upload",
  "question_count": 3,
  "answer": {
    "questions": ["..."],
    "answers": ["..."]
  }
}`}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
