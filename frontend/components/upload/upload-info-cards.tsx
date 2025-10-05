import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fadeInItemMotion, hoverLift, staggeredListMotion } from "@/lib/motion-presets";
import { FileText, ArrowUpFromLine } from "lucide-react";

export function UploadInfoCards() {
  return (
    <motion.div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6" {...staggeredListMotion}>
      <motion.div {...fadeInItemMotion} {...hoverLift}>
        <Card className="card-surface h-full">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-500" />
              <CardTitle className="text-lg font-semibold">Supported Formats</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="font-medium text-foreground flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  Documents
                </div>
                <div className="text-sm text-muted-foreground pl-4">PDF</div>
              </div>
              <div className="space-y-2">
                <div className="font-medium text-foreground flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  Images
                </div>
                <div className="text-sm text-muted-foreground pl-4">PNG, JPG, JPEG, GIF</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div {...fadeInItemMotion} {...hoverLift}>
        <Card className="card-surface h-full">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <ArrowUpFromLine className="w-5 h-5 text-purple-500" />
              <CardTitle className="text-lg font-semibold">Quick Tips</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">Drag files directly from your computer</span>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">Upload multiple files at once</span>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">Files are processed automatically for search</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
