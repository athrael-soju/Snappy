import { ReactNode } from "react"
import { cn } from "@/lib/utils"

import { PageContainer } from "./container"
import { PageBreadcrumb, PageHeader, PageHeaderProps } from "./page-header"

type PageProps = PageHeaderProps & {
  children: ReactNode
  bodyClassName?: string
}

export function Page({
  children,
  bodyClassName,
  ...headerProps
}: PageProps) {
  return (
    <PageContainer className="py-(--space-page-stack)">
      <PageHeader {...headerProps} />
      <PageBody className={bodyClassName}>{children}</PageBody>
    </PageContainer>
  )
}

type PageBodyProps = React.HTMLAttributes<HTMLDivElement>

export function PageBody({ className, ...props }: PageBodyProps) {
  return (
    <div
      className={cn(
        "mt-(--space-page-stack) flex flex-col gap-(--space-page-stack)",
        className
      )}
      {...props}
    />
  )
}

type PageSectionProps = React.ComponentProps<"section"> & {
  inline?: boolean
}

export function PageSection({
  className,
  inline,
  ...props
}: PageSectionProps) {
  return (
    <section
      data-inline={inline ? "true" : undefined}
      className={cn(
        "flex flex-col gap-(--space-section-stack)",
        { "lg:flex-row lg:items-start lg:gap-(--space-page-stack)": inline },
        className
      )}
      {...props}
    />
  )
}

export type { PageBreadcrumb, PageProps }
