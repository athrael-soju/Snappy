import { ReactNode } from "react";
import { motion } from "framer-motion";
import { defaultPageMotion, sectionVariants } from "@/lib/motion-presets";
import { PageHeader } from "@/components/page-header";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface PageLayoutProps {
  children: ReactNode;
  title: string;
  icon?: LucideIcon;
  tooltip?: string;
  description?: string;
  className?: string;
}

export function PageLayout({
  children,
  title,
  icon,
  tooltip,
  description,
  className,
}: PageLayoutProps) {
  // All pages use the same max-width for consistency
  const maxWidthClass = "max-w-6xl";

  return (
    <motion.div
      {...defaultPageMotion}
      className="page-container"
    >
      {/* Header Section */}
      <motion.section variants={sectionVariants} className="page-header-section">
        <PageHeader
          title={title}
          icon={icon}
          tooltip={tooltip}
          description={description}
        />
      </motion.section>

      {/* Content Section */}
      <motion.section
        variants={sectionVariants}
        className="page-content-section"
      >
        <div className={cn("page-content max-w-6xl", className)}>
          {children}
        </div>
      </motion.section>
    </motion.div>
  );
}
