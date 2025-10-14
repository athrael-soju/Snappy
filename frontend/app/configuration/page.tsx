"use client";

import "@/lib/api/client";
import { Settings } from "lucide-react";
import { PageLayout } from "@/components/layout/page-layout";
import { ConfigurationPanel } from "@/components/configuration";

export default function ConfigurationPage() {
  return (
    <PageLayout
      title="System Configuration"
      icon={Settings}
      tooltip="Manage runtime configuration options"
      scrollableContent={true}
    >
      <ConfigurationPanel />
    </PageLayout>
  );
}
