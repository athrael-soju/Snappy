import Link from "next/link"
import { Fragment, ReactNode } from "react"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"

export type PageBreadcrumb = {
  label: string
  href?: string
}

export type PageHeaderProps = {
  title: string
  description?: string
  breadcrumbs?: PageBreadcrumb[]
  actions?: ReactNode
}

export function PageHeader({
  title,
  description,
  breadcrumbs,
  actions,
}: PageHeaderProps) {
  const hasBreadcrumbs = Boolean(breadcrumbs?.length)
  const hasDescription = Boolean(description)
  const hasActions = Boolean(actions)

  return (
    <header className="flex flex-col gap-(--space-section-stack) border-b border-border pb-(--space-section-stack)">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          {hasBreadcrumbs && (
            <Breadcrumb>
              <BreadcrumbList>
                {breadcrumbs!.map((crumb, index) => {
                  const key = `${crumb.href ?? crumb.label}-${index}`
                  const isLast = index === breadcrumbs!.length - 1

                  return (
                    <Fragment key={key}>
                      <BreadcrumbItem>
                        {isLast || !crumb.href ? (
                          <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                        ) : (
                          <BreadcrumbLink asChild>
                            <Link href={crumb.href}>{crumb.label}</Link>
                          </BreadcrumbLink>
                        )}
                      </BreadcrumbItem>
                      {!isLast && <BreadcrumbSeparator />}
                    </Fragment>
                  )
                })}
              </BreadcrumbList>
            </Breadcrumb>
          )}

          <h1 className="text-foreground text-3xl font-semibold tracking-tight">
            {title}
          </h1>
          {hasDescription && (
            <p className="text-muted-foreground text-base leading-relaxed">
              {description}
            </p>
          )}
        </div>

        {hasActions && (
          <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
            {actions}
          </div>
        )}
      </div>
    </header>
  )
}
