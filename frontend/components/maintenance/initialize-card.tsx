import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlayCircle, Loader2 } from "lucide-react";

interface InitializeCardProps {
  isLoading: boolean;
  isSystemReady: boolean;
  isDeleteLoading: boolean;
  onInitialize: () => void;
}

export function InitializeCard({ isLoading, isSystemReady, isDeleteLoading, onInitialize }: InitializeCardProps) {
  return (
    <Card className="min-h-[240px]">
      <CardHeader className="pb-4">
        <div className="mb-3 inline-flex size-12 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
          <PlayCircle className="h-6 w-6" />
        </div>
        <CardTitle className="text-lg font-semibold text-foreground">Initialise system</CardTitle>
        <CardDescription>Create the Qdrant collection and optional MinIO bucket.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed text-muted-foreground">
          Run this before you upload files so Snappy has somewhere to store embeddings and page imagery.
        </p>
        <Button
          onClick={onInitialize}
          disabled={isLoading || isDeleteLoading || isSystemReady}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Initialising…
            </>
          ) : (
            <>
              <PlayCircle className="mr-2 h-4 w-4" />
              Initialise
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
