"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Page, PageSection } from "@/components/layout/page";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

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
    <Page
      title="Home"
      description="A minimal starter template that connects document ingestion, visual embeddings, and conversational search."
    >
      <PageSection>
        <div className="grid gap-(--space-section-stack) sm:grid-cols-2">
          {sections.map((section) => (
            <Card key={section.href} className="h-full">
              <CardHeader className="gap-3">
                <CardTitle className="text-lg">{section.title}</CardTitle>
                <CardDescription>{section.description}</CardDescription>
              </CardHeader>
              <CardFooter className="pt-0">
                <Button
                  asChild
                  variant="ghost"
                  size="sm"
                  className="px-0 text-primary hover:text-primary"
                >
                  <Link href={section.href} className="inline-flex items-center gap-2">
                    Explore
                    <ArrowRight aria-hidden className="size-4" />
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </PageSection>

      <PageSection>
        <Card>
          <CardContent className="space-y-4 text-muted-foreground">
            <p>
              Use the navigation above to upload files, run visual searches, chat over indexed content, or review system
              configuration in one consistent workspace.
            </p>
            <p>
              Backend services stay reachable through the Next.js API client. Update environment variables if the API
              endpoint changes or new credentials are required.
            </p>
          </CardContent>
        </Card>
      </PageSection>
    </Page>
  );
}
