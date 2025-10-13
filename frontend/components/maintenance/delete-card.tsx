import { CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Trash2, AlertTriangle, Loader2 } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass-panel";

interface DeleteCardProps {
  isLoading: boolean;
  isInitLoading: boolean;
  isSystemReady: boolean;
  dialogOpen: boolean;
  onDialogChange: (open: boolean) => void;
  onDelete: () => void;
}

export function DeleteCard({ 
  isLoading, 
  isInitLoading, 
  isSystemReady, 
  dialogOpen, 
  onDialogChange, 
  onDelete 
}: DeleteCardProps) {
  return (
    <GlassPanel className="min-h-[240px] hover:shadow-lg transition-all p-6">
      <CardHeader className="pb-4 px-0 pt-0">
        <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-red-500/10 to-red-500/5 text-red-600 dark:text-red-400 mb-3">
          <Trash2 className="w-6 h-6" />
        </div>
        <CardTitle className="text-xl font-semibold text-foreground">Delete System</CardTitle>
        <CardDescription className="text-base leading-relaxed text-muted-foreground">Remove collection and storage</CardDescription>
      </CardHeader>
      <CardContent className="px-0 pb-0">
        <p className="text-base text-muted-foreground mb-5 leading-relaxed">
          Permanently removes the Qdrant collection and, if enabled, the MinIO bucket. Use this to change configuration or start fresh.
        </p>
        <Dialog open={dialogOpen} onOpenChange={onDialogChange}>
          <DialogTrigger asChild>
            <Button
              variant="destructive"
              disabled={isLoading || isInitLoading || !isSystemReady}
              className="w-full bg-destructive text-destructive-foreground hover:bg-destructive/90 hover:shadow-xl hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 transition-all duration-200 font-semibold rounded-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </>
              )}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Trash2 className="w-5 h-5 text-red-600" />
                Delete Collection and Storage?
              </DialogTitle>
              <DialogDescription className="pt-2">
                This will permanently delete the Qdrant collection and, when enabled, the MinIO bucket, including all vectors, files, and metadata. This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="bg-red-50 dark:bg-red-950/20 p-4 rounded-lg border-l-4 border-red-400">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-base text-red-800 dark:text-red-200 leading-relaxed">
                  <strong>Warning:</strong> All uploaded documents, embeddings, and search indices will be permanently lost.
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => onDialogChange(false)}
                className="border-muted bg-card text-foreground hover:bg-muted hover:text-foreground transition-colors"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={onDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90 hover:shadow-md transition-all"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Confirm Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </GlassPanel>
  );
}
