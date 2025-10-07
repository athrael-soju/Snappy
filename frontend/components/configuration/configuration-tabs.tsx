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
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                  isActive
                    ? 'font-semibold shadow-[var(--nav-pill-shadow)]'
                    : 'text-[color:var(--nav-pill-inactive-foreground,var(--muted-foreground))] hover:bg-[color:var(--nav-pill-hover)] hover:text-[color:var(--nav-pill-hover-foreground,var(--foreground))]'
                }`}
                style={isActive ? {
                  backgroundImage: 'var(--nav-pill-active)',
                  color: 'var(--nav-pill-active-foreground, var(--foreground))'
                } : undefined}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="truncate text-left">{category.name}</span>
              </button>
            );
          })}
        </div>
      </ScrollArea>
    </nav>
  );
}
