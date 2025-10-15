"use client";

import "@/lib/api/client";
import { AppPage } from "@/components/layout";
import { ConfigurationPanel } from "@/components/configuration";

export default function ConfigurationPage() {
  return (
    <AppPage
      title="Configuration"
      description="Manage runtime configuration options for ingestion, retrieval, and system behavior."
    >
      <ConfigurationPanel />
    </AppPage>
  );
}
