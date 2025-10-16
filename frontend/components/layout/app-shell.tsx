import { ReactNode } from "react"

import { PageContainer } from "./container"
import { SiteFooter } from "./site-footer"
import { Nav } from "../nav"

type AppShellProps = {
  children: ReactNode
  sidebar?: ReactNode
  header?: ReactNode
  footer?: ReactNode
}

export function AppShell({
  children,
  sidebar,
  header,
  footer,
}: AppShellProps) {
  const headerContent = header ?? <Nav />
  const footerContent = footer ?? <SiteFooter />

  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <header className="border-b border-border bg-background">
        <PageContainer className="py-4">
          {headerContent}
        </PageContainer>
      </header>

      <div className="flex flex-1 flex-col lg:flex-row">
        {sidebar && (
          <aside className="border-b border-border bg-card/40 lg:h-auto lg:w-64 lg:border-b-0 lg:border-r">
            {sidebar}
          </aside>
        )}

        <main className="flex-1 bg-background">{children}</main>
      </div>

      <footer className="border-t border-border bg-background">
        <PageContainer className="py-(--space-section-stack)">
          {footerContent}
        </PageContainer>
      </footer>
    </div>
  )
}
