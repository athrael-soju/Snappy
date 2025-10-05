"use client";

import AboutContent from "@/components/about-content";
import { PageHeader } from "@/components/page-header";
import { Info } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="page-shell page-section flex flex-col min-h-0 flex-1">
      <PageHeader
        title="About This Template"
        description="A friendly and lightweight knowledge base platform with visual document understanding."
        icon={Info}
      />
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pb-10">
        <AboutContent />
      </div>
    </div>
  );
}
