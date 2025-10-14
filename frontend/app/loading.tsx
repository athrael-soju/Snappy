export default function Loading() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <span
          className="inline-flex size-10 animate-spin rounded-full border-2 border-muted border-t-primary"
          aria-hidden
        />
        <span>Loading...</span>
      </div>
      <span className="sr-only" role="status" aria-live="polite" aria-busy="true">
        Loading
      </span>
    </div>
  );
}
