import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Trash2, AlertTriangle, Loader2 } from "lucide-react";

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
    <Card className="border-red-200/70 dark:border-red-800/60 transition-all duration-300 hover:shadow-lg hover:border-red-300 dark:hover:border-red-700">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-red-100 to-rose-50 dark:from-red-900/40 dark:to-rose-900/30 border-2 border-red-200 dark:border-red-800/50 shadow-sm">
            <Trash2 className="w-5 h-5 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <CardTitle className="text-base font-bold text-red-900 dark:text-red-100">Delete System</CardTitle>
            <CardDescription className="text-xs text-muted-foreground">Remove collection and bucket</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground/85 mb-5 leading-relaxed">
          Permanently deletes the Qdrant collection and MinIO bucket including all data. Use this to change configuration or start fresh.
        </p>
        <Dialog open={dialogOpen} onOpenChange={onDialogChange}>
          <DialogTrigger asChild>
            <Button
              variant="destructive"
              disabled={isLoading || isInitLoading || !isSystemReady}
              className="w-full bg-destructive text-destructive-foreground hover:bg-destructive/90 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold"
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
                Delete Collection and Bucket?
              </DialogTitle>
              <DialogDescription className="pt-2">
                This will permanently delete the Qdrant collection and MinIO bucket, including all vectors, files, and metadata. This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-400">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-800">
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
    </Card>
  );
}
