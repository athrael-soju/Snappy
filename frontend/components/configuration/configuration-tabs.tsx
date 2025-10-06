import { ScrollArea } from "@/components/ui/scroll-area";
import { Settings, Cpu, Brain, Database, HardDrive } from "lucide-react";

interface ConfigCategory {
  name: string;
  description: string;
  order: number;
  icon: string;
  settings: any[];
}

interface ConfigurationTabsProps {
  categories: [string, ConfigCategory][];
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const iconMap: Record<string, any> = {
  settings: Settings,
  cpu: Cpu,
  brain: Brain,
  database: Database,
  "hard-drive": HardDrive,
};

export function ConfigurationTabs({ categories, activeTab, onTabChange }: ConfigurationTabsProps) {
  return (
    <nav className="w-48 flex-shrink-0">
      <ScrollArea className="h-full">
        <div className="space-y-1 pr-2">
          {categories.map(([categoryKey, category]) => {
            const Icon = iconMap[category.icon] || Settings;
            const isActive = activeTab === categoryKey;
            
            return (
              <button
                key={categoryKey}
                onClick={() => onTabChange(categoryKey)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-50 via-purple-50 to-cyan-50 dark:from-blue-900/40 dark:via-purple-900/40 dark:to-blue-900/40 text-blue-800 dark:text-blue-200 border-2 border-blue-300 dark:border-blue-800/50 shadow-lg font-semibold'
                    : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground border-2 border-transparent hover:border-border/50'
                }`}
              >
                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
                <span className="truncate text-left">{category.name}</span>
              </button>
            );
          })}
        </div>
      </ScrollArea>
    </nav>
  );
}
