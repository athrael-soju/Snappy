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
  onDelete,
}: DeleteCardProps) {
  return (
    <Card className="min-h-[240px]">
      <CardHeader className="pb-4">
        <div className="mb-3 inline-flex size-12 items-center justify-center rounded-lg bg-red-100 text-red-600">
          <Trash2 className="h-6 w-6" />
        </div>
        <CardTitle className="text-lg font-semibold text-foreground">Delete system</CardTitle>
        <CardDescription>Remove the Qdrant collection and MinIO bucket.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed text-muted-foreground">
          Use this when you want to start fresh or change configuration that affects indexing.
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
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </>
              )}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-base font-semibold">
                <Trash2 className="h-5 w-5 text-red-600" />
                Delete collection and storage?
              </DialogTitle>
              <DialogDescription>
                This removes all vectors, documents, and stored images. You can re-initialise afterwards.
              </DialogDescription>
            </DialogHeader>
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <p className="text-sm text-red-800">
                  This action cannot be undone.
                </p>
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => onDialogChange(false)} disabled={isLoading}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={onDelete} disabled={isLoading}>
                Confirm delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
