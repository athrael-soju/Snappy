import { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlayCircle, Loader2 } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass-panel";

interface InitializeCardProps {
  isLoading: boolean;
  isSystemReady: boolean;
  isDeleteLoading: boolean;
  onInitialize: () => void;
}

export function InitializeCard({ isLoading, isSystemReady, isDeleteLoading, onInitialize }: InitializeCardProps) {
  return (
    <GlassPanel className="min-h-[240px] hover:shadow-lg transition-all p-6">
      <CardHeader className="pb-4 px-0 pt-0">
        <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5 text-green-600 dark:text-green-400 mb-3">
          <PlayCircle className="w-6 h-6" />
        </div>
        <CardTitle className="text-xl font-semibold text-foreground">Initialize System</CardTitle>
        <CardDescription className="text-base leading-relaxed text-muted-foreground">Create collection and bucket</CardDescription>
      </CardHeader>
      <CardContent className="px-0 pb-0">
        <p className="text-base text-muted-foreground mb-5 leading-relaxed">
          Creates the Qdrant collection and MinIO bucket based on your configuration. Required before uploading files.
        </p>
        <Button
          onClick={onInitialize}
          disabled={isLoading || isDeleteLoading || isSystemReady}
          className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700 hover:shadow-xl hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 transition-all duration-200 font-semibold rounded-full"
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
    </GlassPanel>
  );
}
