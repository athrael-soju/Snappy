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
    <nav className="w-48 flex-shrink-0 min-h-0 flex flex-col">
      <ScrollArea>
        <div className="space-y-1 pr-2">
          {categories.map(([categoryKey, category]) => {
            const Icon = iconMap[category.icon] || Settings;
            const isActive = activeTab === categoryKey;
            
            return (
              <button
                key={categoryKey}
                onClick={() => onTabChange(categoryKey)}
                className={`w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span className="truncate text-left">{category.name}</span>
              </button>
            );
          })}
        </div>
      </ScrollArea>
    </nav>
  );
}
