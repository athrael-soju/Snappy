"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

import { PageHeader } from "./page-header";
import { useAppShell } from "./app-shell";

type BreadcrumbItem = {
  label: string;
  href?: string;
};

interface AppPageProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: ReactNode;
  sidebar?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}

export function AppPage({
  title,
  description,
  breadcrumbs,
  actions,
  sidebar,
  children,
  className,
  contentClassName,
}: AppPageProps) {
  const { setSidebar } = useAppShell();

  useEffect(() => {
    setSidebar(sidebar ?? null);
    return () => {
      setSidebar(null);
    };
  }, [setSidebar, sidebar]);

  return (
    <div className={cn("stack stack-lg", className)}>
      <PageHeader
        title={title}
        description={description}
        breadcrumbs={breadcrumbs}
        actions={actions}
      />
      <div className={cn("section-stack", contentClassName)}>
        {children}
      </div>
    </div>
  );
}
