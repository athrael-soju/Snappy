export default function Loading() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center" role="status" aria-live="polite" aria-busy="true">
      <p className="text-sm text-gray-600">Loading...</p>
    </div>
  );
}

