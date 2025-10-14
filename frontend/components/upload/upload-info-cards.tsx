import { GlassPanel } from "@/components/ui/glass-panel";
import { FileText, Lightbulb } from "lucide-react";

export function UploadInfoCards() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
      <GlassPanel className="p-6 sm:p-8" hover>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex size-14 items-center justify-center rounded-xl icon-bg text-primary">
              <FileText className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold">Supported Formats</h3>
          </div>
          <div className="space-y-3">
            <div>
              <div className="text-sm font-medium mb-1">Documents</div>
              <div className="text-sm text-muted-foreground">PDF</div>
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Images</div>
              <div className="text-sm text-muted-foreground">PNG, JPG, JPEG, GIF</div>
            </div>
          </div>
        </div>
      </GlassPanel>

      <GlassPanel className="p-6 sm:p-8" hover>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex size-14 items-center justify-center rounded-xl icon-bg text-primary">
              <Lightbulb className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold">Quick Tips</h3>
          </div>
          <ul className="space-y-2.5 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="mt-1.5 size-1 rounded-full bg-current flex-shrink-0" />
              <span>Drag files directly from your computer</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 size-1 rounded-full bg-current flex-shrink-0" />
              <span>Upload multiple files at once</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1.5 size-1 rounded-full bg-current flex-shrink-0" />
              <span>Files are processed automatically for search</span>
            </li>
          </ul>
        </div>
      </GlassPanel>
    </div>
  );
}
