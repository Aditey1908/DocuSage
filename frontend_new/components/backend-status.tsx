"use client"

import { useEffect, useState } from "react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000"
const POLL_INTERVAL = 5000 // ms between retries while waking up
const MAX_ATTEMPTS = 24    // ~2 min total

type Status = "checking" | "waking" | "ready" | "error"

export default function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking")
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>

    const ping = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`, {
          signal: AbortSignal.timeout(4000),
        })
        if (res.ok) {
          setStatus("ready")
          return
        }
      } catch {
        // still waking up
      }

      setAttempt((prev) => {
        const next = prev + 1
        if (next >= MAX_ATTEMPTS) {
          setStatus("error")
        } else {
          setStatus("waking")
          timer = setTimeout(ping, POLL_INTERVAL)
        }
        return next
      })
    }

    ping()
    return () => clearTimeout(timer)
  }, [])

  if (status === "ready") {
    return (
      <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700">
        <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
        Backend is up — you&apos;re good to go!
      </div>
    )
  }

  if (status === "error") {
    return (
      <div className="flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700">
        <span className="inline-block h-2 w-2 rounded-full bg-rose-500" />
        Backend unavailable — please try again later
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700">
      <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-amber-500" />
      {status === "checking"
        ? "Connecting to backend…"
        : `Backend is waking up, please wait… (${attempt}/${MAX_ATTEMPTS})`}
    </div>
  )
}
