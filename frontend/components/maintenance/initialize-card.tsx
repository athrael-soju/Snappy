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
    <Card className="border-green-200/70 dark:border-green-800/60 transition-all duration-300 hover:shadow-lg hover:border-green-300 dark:hover:border-green-700">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-green-100 to-emerald-50 dark:from-green-900/40 dark:to-emerald-900/30 border-2 border-green-200 dark:border-green-800/50 shadow-sm">
            <PlayCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <CardTitle className="text-base font-bold text-green-900 dark:text-green-100">Initialize System</CardTitle>
            <CardDescription className="text-xs text-muted-foreground">Create collection and bucket</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground/85 mb-5 leading-relaxed">
          Creates the Qdrant collection and MinIO bucket based on your current configuration settings. Required before uploading files.
        </p>
        <Button
          onClick={onInitialize}
          disabled={isLoading || isDeleteLoading || isSystemReady}
          className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold"
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
