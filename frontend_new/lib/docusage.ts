export const navLinks = [
  { href: "/", label: "Overview" },
  { href: "/upload", label: "Upload" },
  { href: "/workflow", label: "Workflow" },
  { href: "/api", label: "API" },
  { href: "/docs", label: "Docs" },
  { href: "/results", label: "Results" },
]

export const productHighlights = [
  {
    title: "PDF parsing that keeps structure",
    description:
      "DocuSage preserves tables, headings, bullets, and context so the downstream RAG pipeline gets clean input instead of flattened text.",
  },
  {
    title: "Semantic chunking tuned for retrieval",
    description:
      "The chunker keeps related content together, adds context-aware boundaries, and reduces the chance of orphaned answers.",
  },
  {
    title: "Vector search plus reranking",
    description:
      "OpenAI embeddings, Astra DB, and VoyageAI reranking work together to surface the most relevant chunks before the LLM answers.",
  },
  {
    title: "One-pass orchestration",
    description:
      "A single pipeline handles ingestion, embedding, storage, question answering, and cleanup so the app stays easy to operate.",
  },
]

export const workflowSteps = [
  {
    step: "01",
    title: "Ingest document",
    description: "Upload a PDF or provide a URL. The backend downloads or saves the file in a temp workspace.",
  },
  {
    step: "02",
    title: "Extract and chunk",
    description: "pdf_parser.py turns the PDF into structured text and chunker_reworked.py builds retrieval-ready chunks.",
  },
  {
    step: "03",
    title: "Embed and store",
    description: "runner.py embeds every chunk and writes them to Astra DB with request-scoped metadata.",
  },
  {
    step: "04",
    title: "Answer and clean up",
    description: "The app reranks the best chunks, generates answers, returns JSON, and deletes request data.",
  },
]

export const apiRoutes = [
  {
    method: "GET",
    route: "/health",
    description: "Simple readiness probe used by the frontend and deployment checks.",
  },
  {
    method: "POST",
    route: "/process",
    description: "Accepts either JSON with a document URL or multipart form data with an uploaded PDF and questions.",
  },
]

export const envVars = [
  "OPENAI_API_KEY",
  "VOYAGE_API_KEY",
  "ASTRA_DB_ID",
  "ASTRA_DB_REGION",
  "ASTRA_DB_APPLICATION_TOKEN",
  "ASTRA_KEYSPACE",
  "ASTRA_COLLECTION",
  "OPENAI_LLM_MODEL",
  "FRONTEND_URL",
]

export const sampleQuestions = [
  "What is the document about?",
  "Summarize the most important findings.",
  "What limits, exclusions, or waiting periods should I know about?",
]
