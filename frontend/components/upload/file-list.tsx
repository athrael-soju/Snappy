import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { FileText } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ScrollArea } from "@/components/ui/scroll-area";

interface FileListProps {
  files: FileList | null;
  hasFiles: boolean;
}

const fadeIn = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 4 },
};

export function FileList({ files, hasFiles }: FileListProps) {
  return (
    <AnimatePresence>
      {hasFiles && files && (
        <motion.div
          {...fadeIn}
          className="space-y-2"
        >
          <Label className="text-sm font-medium">Selected Files:</Label>
          <ScrollArea className="h-32 w-full rounded-lg border border-muted bg-card">
            <div className="space-y-2 rounded-lg p-3">
              {Array.from(files).map((file, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="flex-1 truncate">{file.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {(file.size / 1024 / 1024).toFixed(1)}MB
                  </Badge>
                </div>
              ))}
            </div>
          </ScrollArea>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

