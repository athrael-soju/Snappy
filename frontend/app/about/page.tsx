"use client";

import { AboutContent } from "@/components/about";
import { AppPage } from "@/components/layout";

export default function AboutPage() {
  return (
    <AppPage
      title="About"
      description="A friendly and lightweight knowledge base platform with visual document understanding."
      contentClassName="stack stack-lg"
    >
      <div className="page-surface p-6 sm:p-8">
        <div className="mx-auto max-w-4xl">
          <AboutContent />
        </div>
      </div>
    </AppPage>
  );
}
