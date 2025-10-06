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
    <Card className="border-2 border-red-200 dark:border-red-800/50 bg-gradient-to-br from-red-500/5 to-pink-500/5">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-red-100 dark:bg-red-900/40 border-2 border-red-200 dark:border-red-800/50">
            <Trash2 className="w-5 h-5 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold text-red-900 dark:text-red-100">Delete System</CardTitle>
            <CardDescription className="text-sm text-muted-foreground">Remove collection and bucket</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground/80 mb-4">
          Permanently deletes the Qdrant collection and MinIO bucket including all data. Use this to change configuration or start fresh.
        </p>
        <Dialog open={dialogOpen} onOpenChange={onDialogChange}>
          <DialogTrigger asChild>
            <Button
              variant="destructive"
              disabled={isLoading || isInitLoading || !isSystemReady}
              className="w-full"
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
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={onDelete}
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
