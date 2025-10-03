import { LucideIcon } from "lucide-react";

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  children?: React.ReactNode;
}

export function PageHeader({ title, description, icon: Icon, children }: PageHeaderProps) {
  return (
    <div className="space-y-3 mb-6 text-center relative">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-20 w-32 h-32 bg-blue-200/20 rounded-full blur-xl" />
        <div className="absolute top-10 right-32 w-24 h-24 bg-purple-200/20 rounded-full blur-xl" />
      </div>
      
      <div className="flex items-center justify-center gap-3 mb-2 relative z-10">
        {Icon && (
          <div className="p-2.5 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-xl border-2 border-blue-200/50 shadow-sm">
            <Icon className="w-6 h-6 text-blue-500" />
          </div>
        )}
        <h1 className="text-4xl font-semibold bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
          {title}
        </h1>
      </div>
      {description && (
        <p className="text-muted-foreground leading-relaxed max-w-2xl mx-auto relative z-10">
          {description}
        </p>
      )}
      {children}
    </div>
  );
}
