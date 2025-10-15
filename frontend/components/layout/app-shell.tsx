"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import { Nav } from "@/components/nav";
import { cn } from "@/lib/utils";

type AppShellContextValue = {
  setSidebar: (sidebar: ReactNode | null) => void;
};

const AppShellContext = createContext<AppShellContextValue | undefined>(undefined);

export function useAppShell() {
  const context = useContext(AppShellContext);

  if (!context) {
    throw new Error("useAppShell must be used within <AppShell />");
  }

  return context;
}

interface AppShellProps {
  children: ReactNode;
  footer?: ReactNode;
}

export function AppShell({ children, footer }: AppShellProps) {
  const [sidebar, setSidebarState] = useState<ReactNode | null>(null);

  const setSidebar = useCallback((content: ReactNode | null) => {
    setSidebarState(content);
  }, []);

  const contextValue = useMemo(
    () => ({
      setSidebar,
    }),
    [setSidebar],
  );

  const year = new Date().getFullYear();

  return (
    <AppShellContext.Provider value={contextValue}>
      <div className="flex min-h-dvh flex-col bg-background text-foreground">
        <Nav />

        {sidebar ? (
          <aside className="app-container stack stack-lg py-6 lg:hidden">
            {sidebar}
          </aside>
        ) : null}

        <main className="flex-1 py-6 lg:py-10">
          <div className="app-container">
            <div
              className={cn(
                "flex flex-col gap-6",
                sidebar &&
                  "lg:flex-row lg:items-start lg:gap-8",
              )}
            >
              <div className="min-w-0 flex-1">{children}</div>
              {sidebar ? (
                <aside className="hidden lg:flex lg:w-[var(--size-sidebar)] lg:flex-col lg:gap-[var(--space-4)]">
                  {sidebar}
                </aside>
              ) : null}
            </div>
          </div>
        </main>

        <footer className="border-t border-border/60 bg-background/80">
          <div className="app-container flex flex-col items-start justify-between gap-2 py-4 text-xs text-muted-foreground sm:flex-row sm:items-center">
            <span>© {year} ColPali Template</span>
            {footer ?? (
              <span>Built with FastAPI, Next.js, and ColPali</span>
            )}
          </div>
        </footer>
      </div>
    </AppShellContext.Provider>
  );
}
