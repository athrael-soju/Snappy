"use client";

export default function AboutPage() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-4">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">About This Template</h1>
        <p className="text-sm text-muted-foreground">
          This project combines a FastAPI backend, a Next.js frontend, and ColPali-powered visual embeddings. The goal of this stripped-down interface is to keep the essential flows available without relying on animation libraries or third-party component toolkits.
        </p>
      </header>

      <section className="space-y-2 rounded border border-border p-4 text-sm leading-relaxed text-muted-foreground">
        <p>
          Document ingestion pushes files to the backend, triggers indexing, and streams progress through server-sent events. Search and chat features query the same vector store so you can jump between keyword retrieval and conversational answers.
        </p>
        <p>
          Configuration and maintenance pages are intentionally basic: they call the same APIs as their earlier counterparts but present the controls as plain form elements. When something goes wrong you can still reset storage, re-run initialization, or tweak environment settings without leaving the browser.
        </p>
        <p>
          Explore the repository to see how each feature is wired. The backend endpoints are generated from OpenAPI definitions, and the stores keep state in a single shared context. You can extend the UI as needed, but this version provides a clean baseline for custom styling.
        </p>
      </section>

      <section className="space-y-2 rounded border border-border p-4 text-sm">
        <h2 className="text-base font-semibold text-foreground">Key Technologies</h2>
        <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
          <li>FastAPI with background workers for indexing and health checks</li>
          <li>Qdrant for vector storage and similarity search</li>
          <li>ColPali models for visual document embeddings</li>
          <li>Next.js for the frontend, using React Server Components and App Router</li>
        </ul>
      </section>
    </main>
  );
}
