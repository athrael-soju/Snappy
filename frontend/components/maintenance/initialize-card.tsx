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
    <Card className="border-2 border-green-200 dark:border-green-800/50 bg-gradient-to-br from-green-500/5 to-emerald-500/5">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-green-100 dark:bg-green-900/40 border-2 border-green-200 dark:border-green-800/50">
            <PlayCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold text-green-900 dark:text-green-100">Initialize System</CardTitle>
            <CardDescription className="text-sm text-muted-foreground">Create collection and bucket</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground/80 mb-4">
          Creates the Qdrant collection and MinIO bucket based on your current configuration settings. Required before uploading files.
        </p>
        <Button
          onClick={onInitialize}
          disabled={isLoading || isDeleteLoading || isSystemReady}
          className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white"
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
