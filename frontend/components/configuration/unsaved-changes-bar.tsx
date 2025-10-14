import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Save, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface UnsavedChangesBarProps {
  hasChanges: boolean;
  saving: boolean;
  modifiedCount: number;
  lastSaved: Date | null;
  onSave: () => void;
  onDiscard: () => void;
}

function formatRelativeTime(date: Date): string {
  const diffMs = Date.now() - date.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diffMs < minute) {
    return "Last saved moments ago.";
  }
  if (diffMs < hour) {
    const minutes = Math.max(1, Math.round(diffMs / minute));
    return `Last saved ${minutes} minute${minutes === 1 ? "" : "s"} ago.`;
  }
  if (diffMs < day) {
    const hours = Math.max(1, Math.round(diffMs / hour));
    return `Last saved ${hours} hour${hours === 1 ? "" : "s"} ago.`;
  }
  const days = Math.max(1, Math.round(diffMs / day));
  return `Last saved ${days} day${days === 1 ? "" : "s"} ago.`;
}

export function UnsavedChangesBar({
  hasChanges,
  saving,
  modifiedCount,
  lastSaved,
  onSave,
  onDiscard,
}: UnsavedChangesBarProps) {
  return (
    <AnimatePresence>
      {hasChanges && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          className="fixed bottom-0 left-0 right-0 z-50 pb-4 px-4 sm:px-6"
        >
          <div className="container max-w-7xl mx-auto">
            <div className="flex flex-col gap-4 rounded-2xl border border-blue-200/70 dark:border-blue-800/50 bg-card/95 backdrop-blur-lg p-4 shadow-xl sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-full bg-primary text-primary-foreground shadow-md">
                  <AlertTriangle className="h-4 w-4" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-foreground sm:text-base">
                      Unsaved configuration changes
                    </p>
                    <Badge variant="outline" className="border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300">
                      {modifiedCount}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground sm:text-sm">
                    You have {modifiedCount} pending change{modifiedCount !== 1 ? 's' : ''}.{' '}
                    {lastSaved ? formatRelativeTime(lastSaved) : "No previous save recorded yet."}
                  </p>
                </div>
              </div>
              <ButtonGroup className="w-full h-full [&>*]:flex-1 sm:w-auto">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onDiscard}
                  disabled={saving}
                  className="border-blue-200 dark:border-blue-800 px-4 py-2 hover:bg-blue-50 dark:hover:bg-blue-950/50 h-full"
                >
                  Discard
                </Button>
                <Button
                  size="sm"
                  onClick={onSave}
                  disabled={saving}
                  className="px-4 py-2 h-full"
                >
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save {modifiedCount} Change{modifiedCount !== 1 ? 's' : ''}
                    </>
                  )}
                </Button>
              </ButtonGroup>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
