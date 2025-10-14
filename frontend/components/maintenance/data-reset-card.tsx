import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { AlertTriangle, Loader2 } from "lucide-react";
import type { MaintenanceAction, ActionType } from "./types";

interface DataResetCardProps {
  action: MaintenanceAction;
  isLoading: boolean;
  isInitLoading: boolean;
  isDeleteLoading: boolean;
  isSystemReady: boolean;
  dialogOpen: boolean;
  onDialogChange: (open: boolean) => void;
  onConfirm: (actionId: ActionType) => void;
}

export function DataResetCard({
  action,
  isLoading,
  isInitLoading,
  isDeleteLoading,
  isSystemReady,
  dialogOpen,
  onDialogChange,
  onConfirm,
}: DataResetCardProps) {
  const Icon = action.icon;

  return (
    <Card className="min-h-[240px]">
      <CardHeader className="pb-4">
        <div className="mb-3 inline-flex size-12 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
          <Icon className="h-6 w-6" />
        </div>
        <CardTitle className="text-lg font-semibold text-foreground">{action.title}</CardTitle>
        <CardDescription className="text-sm text-muted-foreground">{action.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed text-muted-foreground">{action.detailedDescription}</p>
        <Dialog open={dialogOpen} onOpenChange={onDialogChange}>
          <DialogTrigger asChild>
            <Button
              variant="destructive"
              disabled={isInitLoading || isDeleteLoading || !isSystemReady}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Icon className="mr-2 h-4 w-4" />
                  {action.title}
                </>
              )}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-base font-semibold">
                <Icon className="h-5 w-5 text-amber-600" />
                {action.confirmTitle}
              </DialogTitle>
              <DialogDescription className="leading-relaxed">
                {action.confirmMsg}
              </DialogDescription>
            </DialogHeader>
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <p className="text-sm text-amber-800">
                  <strong>Heads up:</strong> this operation cannot be undone.
                </p>
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => onDialogChange(false)} disabled={isLoading}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={() => onConfirm(action.id)} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Icon className="mr-2 h-4 w-4" />
                    Confirm
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
