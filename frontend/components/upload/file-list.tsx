import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface FileListProps {
  files: FileList | null;
  hasFiles: boolean;
}

export function FileList({ files, hasFiles }: FileListProps) {
  return (
    <AnimatePresence>
      {hasFiles && files && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="space-y-2"
        >
          <Label className="text-sm font-medium">Selected Files:</Label>
          <ScrollArea className="h-32 w-full rounded-lg">
            <div className="space-y-2 p-3 bg-muted/30 rounded-lg">
            {Array.from(files).map((file, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <span className="truncate flex-1">{file.name}</span>
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
