"use client"

import { useCallback, useEffect, useRef, type CSSProperties, type MouseEvent, type MutableRefObject, type ReactNode } from "react"

type PageBackgroundProps = {
  children: ReactNode
  className?: string
  style?: CSSProperties
}

function DotGrid({ mousePosRef }: { mousePosRef: MutableRefObject<{ x: number; y: number }> }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const dotsRef = useRef<Array<{ bx: number; by: number; ox: number; oy: number }>>([])
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const context = canvas.getContext("2d")
    if (!context) return

    const spacing = 16
    const dotRadius = 2.4
    const dotColor = "rgba(15, 23, 42, 0.08)"

    const buildGrid = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
      const cols = Math.ceil(canvas.width / spacing) + 2
      const rows = Math.ceil(canvas.height / spacing) + 2
      dotsRef.current = []

      for (let row = 0; row < rows; row += 1) {
        for (let col = 0; col < cols; col += 1) {
          dotsRef.current.push({ bx: col * spacing, by: row * spacing, ox: 0, oy: 0 })
        }
      }
    }

    buildGrid()
    const resizeObserver = new ResizeObserver(buildGrid)
    resizeObserver.observe(canvas)

    const draw = () => {
      const { x: mouseX, y: mouseY } = mousePosRef.current
      const rect = canvas.getBoundingClientRect()
      const canvasMouseX = mouseX - rect.left
      const canvasMouseY = mouseY - rect.top

      const maxDrift = 6
      const radius = 210

      dotsRef.current.forEach((dot) => {
        const dx = dot.bx - canvasMouseX
        const dy = dot.by - canvasMouseY
        const distance = Math.sqrt(dx * dx + dy * dy)
        let targetX = 0
        let targetY = 0

        if (distance < radius && distance > 0) {
          const strength = (1 - distance / radius) * maxDrift
          targetX = (dx / distance) * strength
          targetY = (dy / distance) * strength
        }

        dot.ox += (targetX - dot.ox) * 0.07
        dot.oy += (targetY - dot.oy) * 0.07
      })

      context.clearRect(0, 0, canvas.width, canvas.height)
      context.fillStyle = dotColor
      dotsRef.current.forEach((dot) => {
        context.beginPath()
        context.arc(dot.bx + dot.ox, dot.by + dot.oy, dotRadius, 0, Math.PI * 2)
        context.fill()
      })

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
      resizeObserver.disconnect()
    }
  }, [mousePosRef])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 h-full w-full pointer-events-none"
      style={{ display: "block", zIndex: 0 }}
    />
  )
}

export default function PageBackground({ children, className, style }: PageBackgroundProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const gradientRef = useRef<HTMLDivElement | null>(null)
  const mousePosRef = useRef({ x: -9999, y: -9999 })

  const handleMouseMove = useCallback((event: MouseEvent<HTMLDivElement>) => {
    mousePosRef.current = { x: event.clientX, y: event.clientY }

    if (gradientRef.current && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      gradientRef.current.style.left = `${event.clientX - rect.left}px`
      gradientRef.current.style.top = `${event.clientY - rect.top}px`
    }
  }, [])

  const handleMouseLeave = useCallback(() => {
    mousePosRef.current = { x: -9999, y: -9999 }
  }, [])

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ position: "relative", ...style }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <DotGrid mousePosRef={mousePosRef} />

      <div
        ref={gradientRef}
        className="pointer-events-none absolute left-1/2 top-1/2"
        style={{
          width: 408,
          height: 408,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(225, 200, 148, 0.32) 0%, rgba(235, 218, 178, 0.18) 40%, transparent 72%)",
          transform: "translate(-50%, -50%)",
          willChange: "left, top",
          zIndex: 0,
        }}
      />

      <div className="relative z-10">{children}</div>
    </div>
  )
}
