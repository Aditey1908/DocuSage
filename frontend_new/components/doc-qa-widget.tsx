"use client"

import { useMemo, useState, type FormEvent } from "react"
import { ArrowRight, FileUp, Link2, Loader2, Sparkles, X } from "lucide-react"

import { sampleQuestions } from "@/lib/docusage"

type AnswerPayload = {
  questions?: string[]
  answers?: string[]
  raw_output?: string
}

type RunnerResult = {
  answer?: AnswerPayload
  session_id?: string
  source_type?: string
  question_count?: number
  error?: string
  details?: string
}

function ResultChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-900">{value}</p>
    </div>
  )
}

function FormattedText({ text }: { text: string }) {
  if (!text) return null
  const parts = text.split(/(\*\*.*?\*\*)/g)
  
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={index} className="font-semibold text-slate-900">
              {part.slice(2, -2)}
            </strong>
          )
        }
        return <span key={index}>{part}</span>
      })}
    </>
  )
}

export default function DocQAWidget() {
  const [inputMode, setInputMode] = useState<"upload" | "url">("upload")
  const [documentUrl, setDocumentUrl] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [questionsText, setQuestionsText] = useState(sampleQuestions.join("\n"))
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RunnerResult | null>(null)
  const [showForm, setShowForm] = useState(true)

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000"

  const questions = useMemo(
    () => questionsText.split("\n").map((question) => question.trim()).filter(Boolean),
    [questionsText],
  )

  const answerPayload = result?.answer
  const answerCards = answerPayload?.answers?.map((answer, index) => ({
    question: questions[index] ?? `Question ${index + 1}`,
    answer,
  }))

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!questions.length) {
      setResult({ error: "Add at least one question." })
      setShowForm(false)
      return
    }

    if (inputMode === "upload" && !file) {
      setResult({ error: "Please upload a PDF file." })
      setShowForm(false)
      return
    }

    if (inputMode === "url" && !documentUrl.trim()) {
      setResult({ error: "Please provide a PDF URL." })
      setShowForm(false)
      return
    }

    try {
      setLoading(true)
      setResult(null)
      setShowForm(false)

      let body: BodyInit
      let headers: HeadersInit | undefined

      if (inputMode === "upload" && file) {
        const formData = new FormData()
        formData.append("document", file)
        formData.append("questions", JSON.stringify(questions))
        body = formData
      } else {
        headers = { "Content-Type": "application/json" }
        body = JSON.stringify({ documents: documentUrl.trim(), questions })
      }

      const response = await fetch(`${API_BASE}/process`, {
        method: "POST",
        headers,
        body,
      })

      const data = (await response.json()) as RunnerResult
      setResult(data)
    } catch (error) {
      setResult({ error: error instanceof Error ? error.message : String(error) })
      setShowForm(false)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setShowForm(true)
    setFile(null)
    setDocumentUrl("")
    setQuestionsText(sampleQuestions.join("\n"))
  }

  // Show results full-width when available
  if (result && !showForm) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-50/95 px-4 py-12 sm:px-6 lg:px-8 backdrop-blur-sm">
        <div className="mx-auto w-full max-w-5xl">
          <div className="rounded-[36px] border border-slate-200 bg-white p-6 sm:p-10 shadow-2xl">
            <div className="mb-8 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Results</p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Your answers</h2>
            </div>
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-200"
            >
              <ArrowRight className="size-4 rotate-180" />
              Ask another
            </button>
          </div>

          {result.error ? (
            <div className="rounded-[24px] border border-rose-200 bg-rose-50 p-6 text-sm leading-6 text-rose-900">
              <p className="font-semibold">Error</p>
              <p className="mt-2">{result.error}</p>
              {result.details ? <pre className="mt-3 overflow-auto text-xs text-rose-700">{result.details}</pre> : null}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-3">
                <ResultChip label="Session ID" value={result.session_id?.slice(0, 12) + "..." ?? "-"} />
                <ResultChip label="Total Questions" value={String(result.question_count ?? questions.length)} />
                <ResultChip label="Source Type" value={result.source_type ?? "-"} />
              </div>

              {answerCards?.length ? (
                <div className="space-y-4">
                  {answerCards.map((card, index) => (
                    <div
                      key={`${index}-${card.question}`}
                      className="rounded-[24px] border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-6 shadow-sm transition hover:shadow-md"
                    >
                      <div className="mb-3 flex items-baseline gap-3">
                        <span className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Q{index + 1}</span>
                        <p className="text-sm font-semibold text-slate-900">{card.question}</p>
                      </div>
                      <p className="text-sm leading-7 text-slate-700 whitespace-pre-wrap">
                        <FormattedText text={card.answer ?? ""} />
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-[24px] border border-slate-200 bg-slate-950 p-6 text-slate-100">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Raw response</p>
                  <pre className="mt-4 overflow-auto text-xs leading-6 text-slate-300">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-3xl">
      <form onSubmit={handleSubmit} className="rounded-[32px] border border-slate-200 bg-white/80 p-6 sm:p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-emerald-700">Live Demo</p>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-950">Analyze a PDF Document</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Choose to upload a file or provide a URL to automatically run a comprehensive document analysis.
          </p>
        </div>

        {/* Input Mode Tabs */}
        <div className="mb-6 flex gap-2 rounded-full border border-slate-200 bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setInputMode("upload")}
            className={`flex-1 rounded-full px-4 py-2 text-sm font-medium transition ${
              inputMode === "upload"
                ? "bg-white text-slate-950 shadow-sm"
                : "text-slate-600 hover:text-slate-950"
            }`}
          >
            <FileUp className="mr-2 inline-block size-4" />
            Upload File
          </button>
          <button
            type="button"
            onClick={() => setInputMode("url")}
            className={`flex-1 rounded-full px-4 py-2 text-sm font-medium transition ${
              inputMode === "url"
                ? "bg-white text-slate-950 shadow-sm"
                : "text-slate-600 hover:text-slate-950"
            }`}
          >
            <Link2 className="mr-2 inline-block size-4" />
            Use URL
          </button>
        </div>

        {/* Document Input - Clean Single Choice */}
        <div className="mb-6">
          {inputMode === "upload" ? (
            <label className="grid gap-3">
              <div className="text-sm font-medium text-slate-700">Select a PDF file</div>
              <div className="flex flex-col items-center justify-center rounded-[24px] border-2 border-dashed border-slate-300 bg-slate-50/50 px-6 py-8 transition hover:border-slate-400 hover:bg-slate-100/50">
                <FileUp className="mb-3 size-8 text-slate-400" />
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  className="absolute w-0 opacity-0"
                  aria-hidden="true"
                />
                <p className="text-sm font-medium text-slate-900">{file ? file.name : "Click to select or drag a PDF"}</p>
                <p className="mt-1 text-xs text-slate-500">PDF files up to 50MB</p>
              </div>
            </label>
          ) : (
            <label className="grid gap-3">
              <div className="text-sm font-medium text-slate-700">PDF URL</div>
              <div className="flex items-center gap-3 rounded-[24px] border border-slate-200 bg-white px-4 py-3 shadow-sm transition hover:border-slate-300">
                <Link2 className="size-4 text-slate-400" />
                <input
                  value={documentUrl}
                  onChange={(event) => setDocumentUrl(event.target.value)}
                  placeholder="https://example.com/document.pdf"
                  className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
                />
              </div>
              <p className="text-xs text-slate-500">Enter the full URL to a publicly accessible PDF</p>
            </label>
          )}
        </div>



        {/* Questions */}
        <div className="mb-6">
          <label className="grid gap-3 mb-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-slate-700">Questions (one per line)</div>
              <label className="cursor-pointer rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 transition hover:bg-emerald-100">
                Upload .txt
                <input 
                  type="file" 
                  accept=".txt" 
                  className="hidden" 
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    const reader = new FileReader();
                    reader.onload = (ev) => {
                      const text = ev.target?.result;
                      if (typeof text === "string") setQuestionsText(text);
                    };
                    reader.readAsText(f);
                  }}
                />
              </label>
            </div>
            <textarea
              value={questionsText}
              onChange={(event) => setQuestionsText(event.target.value)}
              rows={4}
              className="rounded-[24px] border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-emerald-400 focus:ring-1 focus:ring-emerald-300"
              placeholder="What is the main topic?&#10;What are the key findings?"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.slice(0, 3).map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => setQuestionsText(sampleQuestions.join("\n"))}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-300 hover:bg-white"
              >
                {question.length > 30 ? question.slice(0, 30) + "..." : question}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={loading || (inputMode === "upload" ? !file : !documentUrl.trim())}
            className="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Sparkles className="size-4" />
                Run Analysis
              </>
            )}
          </button>
          <p className="text-xs text-slate-500">Uses the Flask backend API</p>
        </div>
      </form>
    </div>
  )
}
