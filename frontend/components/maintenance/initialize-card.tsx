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
    <Card className="card-surface min-h-[240px] border-green-200/70 dark:border-green-800/60 hover:border-green-300 dark:hover:border-green-700">
      <CardHeader className="pb-4">
        <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5 text-green-600 dark:text-green-400 mb-3">
          <PlayCircle className="w-6 h-6" />
        </div>
        <CardTitle className="text-xl font-semibold text-foreground">Initialize System</CardTitle>
        <CardDescription className="text-base leading-relaxed text-muted-foreground">Create collection and bucket</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-base text-muted-foreground mb-5 leading-relaxed">
          Creates the Qdrant collection and MinIO bucket based on your configuration. Required before uploading files.
        </p>
        <Button
          onClick={onInitialize}
          disabled={isLoading || isDeleteLoading || isSystemReady}
          className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700 hover:shadow-lg disabled:opacity-50 transition-all font-semibold rounded-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Initializing...
            </>
          ) : (
            <>
              <PlayCircle className="w-4 h-4 mr-2" />
              Initialize
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
