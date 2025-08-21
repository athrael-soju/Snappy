export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-96">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        <span className="text-muted-foreground">Loading...</span>
      </div>
    </div>
  );
}
