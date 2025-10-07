import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CheckCircle, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { fadeInPresence } from "@/lib/motion-presets";

interface UploadStatusAlertsProps {
  message: string | null;
  error: string | null;
}

export function UploadStatusAlerts({ message, error }: UploadStatusAlertsProps) {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          variants={fadeInPresence}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          <Alert variant="default" className="border-green-200 bg-green-50/50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-800">Upload Status</AlertTitle>
            <AlertDescription className="text-green-700">{message}</AlertDescription>
          </Alert>
        </motion.div>
      )}
      
      {error && (
        <motion.div
          variants={fadeInPresence}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Upload Status</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
