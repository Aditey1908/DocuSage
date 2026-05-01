import { BadgeCheck, MessageSquareQuote, ShieldCheck } from "lucide-react"

function ResultCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[24px] border border-orange-200/50 bg-gradient-to-br from-orange-50 to-amber-50/30 p-5 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-orange-700">{title}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{description}</p>
    </div>
  )
}

export default function ResultsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8 lg:py-16">
      <div className="rounded-[36px] border border-slate-200 bg-white/80 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] sm:p-10 backdrop-blur-[18px]">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-orange-200 bg-orange-50 px-4 py-2 text-sm font-medium text-orange-700 shadow-sm">
            <MessageSquareQuote className="size-4" />
            Output view
          </div>
          <h1 className="mt-6 font-serif text-5xl tracking-tight text-slate-950 sm:text-6xl">
            Read DocuSage output without digging through logs.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
            This page shows the shape of the answer payload returned by the pipeline so users know what to expect
            after they click submit.
          </p>
        </div>

        <div className="mt-10 grid gap-4 xl:grid-cols-3">
          <ResultCard
            title="Session metadata"
            description="Each run returns a unique session id, the input source type, and the number of questions processed."
          />
          <ResultCard
            title="Answer array"
            description="Responses are returned as an ordered answer list that matches the questions submitted to the API."
          />
          <ResultCard
            title="Cleanup state"
            description="The backend removes request-specific chunks from Astra DB once the run has finished."
          />
        </div>

        <div className="mt-10 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
          <div className="rounded-[24px] border border-orange-200/50 bg-gradient-to-br from-orange-950 to-amber-950 p-5 text-orange-50 shadow-[0_20px_60px_rgba(15,23,42,0.18)]">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-orange-300">Example payload</p>
            <pre className="mt-4 overflow-auto text-xs leading-6 text-orange-100">{`{
  "session_id": "934e38b4-...",
  "source_type": "upload",
  "question_count": 3,
  "answer": {
    "questions": ["What is the document about?"],
    "answers": ["The document describes ..."]
  }
}`}</pre>
          </div>

          <div className="grid gap-4">
            <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
              <BadgeCheck className="size-5 text-emerald-700" />
              <h3 className="mt-4 text-lg font-semibold text-slate-950">What a good run looks like</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                The response contains a stable session id, answers that correspond to each question, and no raw vector
                database records leaking into the UI.
              </p>
            </div>

            <div className="rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm">
              <ShieldCheck className="size-5 text-emerald-700" />
              <h3 className="mt-4 text-lg font-semibold text-slate-950">Why the cleanup matters</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Request-scoped cleanup keeps the Astra collection tidy and makes repeated testing safe.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
