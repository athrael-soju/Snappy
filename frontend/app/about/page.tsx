"use client"

import { Page, PageSection } from "@/components/layout/page"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export default function AboutPage() {
  return (
    <Page
      title="About"
      description="This template combines a FastAPI backend, a Next.js frontend, and ColPali-powered visual embeddings."
    >
      <PageSection>
        <Card>
          <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
            <p>
              Document ingestion pushes files to the backend, triggers indexing, and streams progress through
              server-sent events. Search and chat features query the same vector store so you can jump between keyword
              retrieval and conversational answers.
            </p>
            <p>
              Configuration and maintenance pages call the same APIs as their earlier counterparts but present the
              controls as streamlined forms. When something goes wrong you can reset storage, re-run initialization, or
              tweak environment settings without leaving the browser.
            </p>
            <p>
              Explore the repository to see how each feature is wired. Backend endpoints are generated from OpenAPI
              definitions, and shared stores keep state in a single context. Extend the UI as needed—this version
              provides a clean baseline for custom styling.
            </p>
          </CardContent>
        </Card>
      </PageSection>

      <PageSection>
        <Card>
          <CardHeader className="gap-2">
            <CardTitle className="text-base">Key technologies</CardTitle>
            <CardDescription>
              Core pieces that power the template across ingestion, retrieval, and presentation.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
              <li>FastAPI with background workers for indexing and health checks</li>
              <li>Qdrant for vector storage and similarity search</li>
              <li>ColPali models for visual document embeddings</li>
              <li>Next.js for the frontend using React Server Components and the App Router</li>
            </ul>
          </CardContent>
        </Card>
      </PageSection>
    </Page>
  )
}
