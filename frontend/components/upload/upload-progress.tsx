import { Progress } from "@/components/ui/progress";
import { motion, AnimatePresence } from "framer-motion";
import { fadeInPresence } from "@/lib/motion-presets";

interface UploadProgressProps {
  uploading: boolean;
  progress: number;
  statusText: string | null;
  jobId: string | null;
}

export function UploadProgress({ uploading, progress, statusText, jobId }: UploadProgressProps) {
  return (
    <AnimatePresence>
      {uploading && (
        <motion.div
          variants={fadeInPresence}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="space-y-2"
        >
          <div className="flex items-center justify-between text-sm">
            <span>
              {statusText || (jobId ? `Indexing job ${jobId.slice(0, 8)}...` : 'Uploading...')}
            </span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
