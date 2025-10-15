"use client";

import Link from "next/link";

const sections = [
  {
    title: "Upload Documents",
    description: "Add files to the index so they can be searched and discussed.",
    href: "/upload",
  },
  {
    title: "Search",
    description: "Look up indexed content with plain text queries.",
    href: "/search",
  },
  {
    title: "Chat",
    description: "Ask questions about your documents in a conversational interface.",
    href: "/chat",
  },
  {
    title: "Configuration",
    description: "Review and adjust backend configuration values.",
    href: "/configuration",
  },
  {
    title: "Maintenance",
    description: "Check system status and run reset operations when needed.",
    href: "/maintenance",
  },
  {
    title: "About",
    description: "Learn more about this FastAPI, Next.js, and ColPali starter project.",
    href: "/about",
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-8 p-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">FastAPI / Next.js / ColPali Template</h1>
        <p className="text-sm text-muted-foreground">
          A minimal starter project that wires together document ingestion, visual embeddings, and conversational search.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-foreground">Getting Around</h2>
        <ul className="grid gap-3 sm:grid-cols-2">
          {sections.map((section) => (
            <li key={section.href} className="rounded border border-border p-4 transition-colors hover:border-primary">
              <Link href={section.href} className="flex flex-col gap-2">
                <span className="text-base font-medium text-primary">{section.title}</span>
                <span className="text-sm text-muted-foreground">{section.description}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-2 text-sm leading-relaxed text-muted-foreground">
        <p>
          This stripped-down interface keeps the essential flows available without animations or component libraries. Use the navigation above to upload files, run searches, chat over indexed content, or manage configuration.
        </p>
        <p>
          Backend services are reachable through the Next.js API client. Update your environment variables if the API endpoint changes.
        </p>
      </section>
    </main>
  );
}
