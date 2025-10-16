import { cn } from "@/lib/utils"

type ContainerProps = React.HTMLAttributes<HTMLDivElement>

export function PageContainer({ className, ...props }: ContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full max-w-(--container-page) px-(--space-container-inline)",
        className
      )}
      {...props}
    />
  )
}
