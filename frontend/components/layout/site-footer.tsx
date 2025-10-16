export function SiteFooter() {
  return (
    <div className="flex flex-col gap-2 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
      <span>
        © {new Date().getFullYear()} ColPali Template. All rights reserved.
      </span>
      <span>Built with FastAPI, Next.js, and ColPali.</span>
    </div>
  )
}
