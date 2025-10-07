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
    <Card className="border-amber-200/70 dark:border-amber-800/60 transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-100 dark:bg-amber-900/40 border-2 border-amber-200 dark:border-amber-800/50">
            <Icon className="w-5 h-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold text-amber-900 dark:text-amber-100">{action.title}</CardTitle>
            <CardDescription className="text-sm text-muted-foreground">{action.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground/80 mb-4">
          {action.detailedDescription}
        </p>
        <Dialog open={dialogOpen} onOpenChange={onDialogChange}>
          <DialogTrigger asChild>
            <Button
              variant="destructive"
              disabled={isInitLoading || isDeleteLoading || !isSystemReady}
              className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Icon className="w-4 h-4 mr-2" />
                  {action.title}
                </>
              )}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-lg">
                <Icon className="w-5 h-5 text-amber-600" />
                {action.confirmTitle}
              </DialogTitle>
              <DialogDescription className="leading-relaxed pt-2 max-w-prose">
                {action.confirmMsg}
              </DialogDescription>
            </DialogHeader>
            <div className="bg-amber-50 p-4 rounded-lg border-l-4 border-amber-400">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-amber-800 leading-relaxed">
                  <strong>Warning:</strong> This operation cannot be reversed. The system will return to its initial empty state.
                </p>
              </div>
            </div>
            <DialogFooter className="gap-2">
              <Button
                variant="outline"
                onClick={() => onDialogChange(false)}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => onConfirm(action.id)}
                disabled={isLoading}
                className="bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Icon className="w-4 h-4 mr-2" />
                    Confirm {action.title}
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
