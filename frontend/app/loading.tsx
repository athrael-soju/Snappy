import { Spinner } from "@/components/ui/spinner";

export default function Loading() {
  return (
    <div className="min-h-svh grid place-items-center">
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <Spinner size={24} />
        <span>Loading...</span>
      </div>
    </div>
  );
}
