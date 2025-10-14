import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, ArrowUpFromLine } from "lucide-react";

const containerMotion = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.25, ease: "easeOut" },
};

const itemMotion = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
};

export function UploadInfoCards() {
  return (
    <motion.div
      {...containerMotion}
      className="grid gap-4 sm:grid-cols-2"
    >
      <motion.div variants={itemMotion} initial="initial" animate="animate">
        <Card className="h-full">
          <CardHeader className="space-y-3">
            <div className="flex size-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-6 w-6" />
            </div>
            <CardTitle className="text-lg font-semibold">Supported formats</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div>
              <span className="font-medium text-foreground">Documents</span>
              <p>PDF</p>
            </div>
            <div>
              <span className="font-medium text-foreground">Images</span>
              <p>PNG, JPG, JPEG, GIF</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={itemMotion} initial="initial" animate="animate">
        <Card className="h-full">
          <CardHeader className="space-y-3">
            <div className="flex size-12 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
              <ArrowUpFromLine className="h-6 w-6" />
            </div>
            <CardTitle className="text-lg font-semibold">Quick tips</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>Drag files straight into the dropzone or click Browse.</p>
            <p>Batch uploads are supported—Snappy queues the work for you.</p>
            <p>Once processed, files appear in search and chat automatically.</p>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
