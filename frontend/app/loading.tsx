export default function Loading() {
  return (
    <div className="relative flex items-center justify-center min-h-[60vh]">
      <div className="pointer-events-none absolute inset-0 -z-10 opacity-70">
        <div className="absolute -top-24 -left-24 h-64 w-64 rounded-full bg-gradient-to-br from-blue-200/40 via-purple-200/40 to-cyan-200/40 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-64 w-64 rounded-full bg-gradient-to-tr from-cyan-200/40 via-purple-200/40 to-blue-200/40 blur-3xl" />
      </div>
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-600 via-purple-600 to-cyan-500 p-[2px] animate-spin">
            <div className="w-full h-full rounded-full bg-background"></div>
          </div>
          <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-blue-600/20 via-purple-600/20 to-cyan-500/20 blur-md"></div>
        </div>
        <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent font-medium">
          Loading...
        </span>
      </div>
      <span className="sr-only" role="status" aria-live="polite" aria-busy="true">Loading</span>
    </div>
  );
}
