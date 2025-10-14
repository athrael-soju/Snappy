import { Settings, Cpu, Brain, Database, HardDrive } from "lucide-react";
import { GlassPanel } from "@/components/ui/glass-panel";

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
    <nav className="flex justify-center">
      <GlassPanel className="inline-flex p-1.5 sm:p-2">
        <div className="flex flex-wrap justify-center gap-1 sm:gap-2">
          {categories.map(([categoryKey, category]) => {
            const Icon = iconMap[category.icon] || Settings;
            const isActive = activeTab === categoryKey;
            
            return (
              <button
                key={categoryKey}
                onClick={() => onTabChange(categoryKey)}
                className={`flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                }`}
              >
                <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
                <span className="hidden sm:inline whitespace-nowrap">{category.name}</span>
              </button>
            );
          })}
        </div>
      </GlassPanel>
    </nav>
  );
}
