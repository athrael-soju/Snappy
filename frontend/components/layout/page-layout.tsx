import { ReactNode } from "react";
import { motion } from "framer-motion";
import { defaultPageMotion, sectionVariants } from "@/lib/motion-presets";
import { PageHeader } from "@/components/page-header";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassPanel } from "@/components/ui/glass-panel";

interface PageLayoutProps {
  children: ReactNode;
  title: string;
  icon?: LucideIcon;
  tooltip?: string;
  description?: string;
  className?: string;
  /** If true, wraps content in a scrollable panel. Default: false */
  scrollableContent?: boolean;
  /** Max width for content. Default: 1160px */
  maxWidth?: string;
}

export function PageLayout({
  children,
  title,
  icon,
  tooltip,
  description,
  className,
  scrollableContent = false,
  maxWidth = "1160px",
}: PageLayoutProps) {
  return (
    <motion.div {...defaultPageMotion} className={cn("mx-auto w-full h-full px-4 sm:px-6 lg:px-8")} style={{ maxWidth }}>
      {/* Page stack */}
      <div className="flex h-full flex-col gap-4 sm:gap-6 py-4 sm:py-6">
        {/* Header card */}
        <motion.div variants={sectionVariants} className="flex-shrink-0">
          <GlassPanel className="p-3 sm:p-4">
            <div className="flex items-center gap-2 sm:gap-3">
              {icon && (
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500">
                  {(() => {
                    const Icon = icon;
                    return <Icon className="h-5 w-5 text-white" />;
                  })()}
                </div>
              )}
              <div className="flex-1">
                <h1 className="text-xl font-semibold">{title}</h1>
                {description && <p className="text-sm text-muted-foreground">{description}</p>}
                {tooltip && !description && <p className="text-sm text-muted-foreground">{tooltip}</p>}
              </div>
            </div>
          </GlassPanel>
        </motion.div>

        {/* Content section */}
        <motion.div variants={sectionVariants} className={cn("flex-1 min-h-0", className)}>
          {scrollableContent ? (
            <div 
              className="h-full overflow-y-auto px-2 sm:px-4 py-4"
              style={{ overscrollBehavior: 'contain', scrollbarGutter: 'stable' }}
            >
              {children}
            </div>
          ) : (
            children
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}
