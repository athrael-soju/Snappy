import { FileText, Lightbulb, Image, FileType } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass-panel";

export function UploadInfoCards() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Supported Formats */}
      <GlassPanel className="p-5">
        <div className="space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <FileText className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold">Supported Formats</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="inline-flex items-center gap-1.5 rounded-full border bg-background/50 px-3 py-2 text-xs">
              <FileType className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="font-medium">PDF</span>
            </div>
            <div className="inline-flex items-center gap-1.5 rounded-full border bg-background/50 px-3 py-2 text-xs">
              <Image className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="font-medium">PNG, JPG, JPEG, GIF</span>
            </div>
          </div>
        </div>
      </GlassPanel>

      {/* Quick Tips */}
      <GlassPanel className="p-5">
        <div className="space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Lightbulb className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold">Quick Tips</h3>
          </div>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="mt-1.5 size-1.5 rounded-full bg-current flex-shrink-0" />
              <span>Drag files directly from your computer</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 size-1.5 rounded-full bg-current flex-shrink-0" />
              <span>Upload multiple files at once</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 size-1.5 rounded-full bg-current flex-shrink-0" />
              <span>Files are processed automatically for search</span>
            </li>
          </ul>
        </div>
      </GlassPanel>
    </div>
  );
}
