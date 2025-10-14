import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";

export interface ConfigSetting {
  key: string;
  label: string;
  type: "text" | "number" | "boolean" | "select" | "password";
  options?: string[];
  default: string;
  description: string;
  help_text?: string;
  min?: number;
  max?: number;
  step?: number;
  depends_on?: {
    key: string;
    value: boolean;
  };
  ui_hidden?: boolean;
}

interface SettingRendererProps {
  setting: ConfigSetting;
  value: string;
  saving: boolean;
  isNested?: boolean;
  onChange: (key: string, value: string) => void;
}

export function SettingRenderer({ setting, value, saving, isNested = false, onChange }: SettingRendererProps) {
  const currentValue = value || setting.default;

  // Nested settings have compact styling
  if (isNested) {
    switch (setting.type) {
      case "boolean":
        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-4">
              <Label htmlFor={setting.key} className="text-xs font-medium flex items-center gap-1.5">
                {setting.label}
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                        <p className="text-xs">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </Label>
              <Switch
                id={setting.key}
                checked={currentValue.toLowerCase() === "true"}
                onCheckedChange={(checked) => onChange(setting.key, checked ? "True" : "False")}
                disabled={saving}
                className="scale-90"
              />
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">{setting.description}</p>
          </div>
        );
      case "number":
        const numValue = parseFloat(currentValue) || parseFloat(setting.default);
        const min = setting.min ?? 0;
        const max = setting.max ?? 100;
        const step = setting.step ?? 1;

        return (
          <div className="space-y-2.5">
            <Label htmlFor={setting.key} className="text-xs font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                      <p className="text-xs">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <div className="flex items-center gap-3">
              <Slider
                id={setting.key}
                value={[numValue]}
                min={min}
                max={max}
                step={step}
                onValueChange={(vals) => onChange(setting.key, vals[0].toString())}
                disabled={saving}
                className="flex-1"
              />
              <Input
                type="number"
                value={currentValue}
                onChange={(e) => onChange(setting.key, e.target.value)}
                min={min}
                max={max}
                step={step}
                disabled={saving}
                className="w-20 h-9 text-sm"
              />
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">{setting.description}</p>
          </div>
        );
      case "text":
      case "password":
        return (
          <div className="space-y-2">
            <Label htmlFor={setting.key} className="text-xs font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                      <p className="text-xs">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <Input
              id={setting.key}
              type={setting.type === "password" ? "password" : "text"}
              value={currentValue}
              onChange={(e) => onChange(setting.key, e.target.value)}
              disabled={saving}
              className="h-9 text-sm"
            />
            <p className="text-xs text-muted-foreground leading-relaxed">{setting.description}</p>
          </div>
        );
      case "select":
        return (
          <div className="space-y-2">
            <Label htmlFor={setting.key} className="text-xs font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                      <p className="text-xs">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <Select
              value={currentValue}
              onValueChange={(val) => onChange(setting.key, val)}
              disabled={saving}
            >
              <SelectTrigger className="h-9 text-sm">
                <SelectValue placeholder={setting.label} />
              </SelectTrigger>
              <SelectContent>
                {(setting.options ?? []).map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground leading-relaxed">{setting.description}</p>
          </div>
        );
      default:
        return null;
    }
  }

  // Two-column layout: label+description left, control right
  switch (setting.type) {
    case "boolean":
      return (
        <div className="py-4 space-y-2">
          <div className="flex items-center justify-between gap-8">
            <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <Switch
              id={setting.key}
              checked={currentValue.toLowerCase() === "true"}
              onCheckedChange={(checked) => onChange(setting.key, checked ? "True" : "False")}
              disabled={saving}
            />
          </div>
          <p className="text-sm text-muted-foreground">{setting.description}</p>
        </div>
      );

    case "select":
      return (
        <div className="flex flex-col gap-4 py-4 sm:flex-row sm:items-start sm:gap-6">
          <div className="space-y-1 sm:flex-1">
            <Label htmlFor={setting.key} className="flex items-center gap-1.5 text-sm font-medium">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="h-3.5 w-3.5 cursor-help text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="border-border bg-popover text-popover-foreground">
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">{setting.description}</p>
          </div>
          <div className="w-full sm:min-w-[220px] sm:max-w-[280px]">
            <Select
              value={currentValue}
              onValueChange={(value) => onChange(setting.key, value)}
              disabled={saving}
            >
              <SelectTrigger id={setting.key} className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {setting.options?.map(option => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      );

    case "number": {
      const sliderMin = setting.min ?? 0;
      const sliderMax = setting.max ?? 100;
      const sliderStep = setting.step ?? 1;
      const parsed = parseFloat(currentValue);
      const numValue = Number.isNaN(parsed) ? parseFloat(setting.default) : parsed;
      const hasRange = typeof setting.min === "number" || typeof setting.max === "number";
      const rangeMinText = typeof setting.min === "number" ? setting.min : "min";
      const rangeMaxText = typeof setting.max === "number" ? setting.max : "max";

      return (
        <div className="flex flex-col gap-4 py-4 sm:flex-row sm:items-start sm:gap-6">
          <div className="space-y-1 sm:flex-1">
            <Label htmlFor={setting.key} className="flex items-center gap-1.5 text-sm font-medium">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="h-3.5 w-3.5 cursor-help text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="border-border bg-popover text-popover-foreground">
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">
              {setting.description}
              {hasRange && (
                <span className="ml-1 text-xs text-muted-foreground">
                  ({rangeMinText} to {rangeMaxText})
                </span>
              )}
            </p>
          </div>
          <div className="w-full sm:min-w-[220px] sm:max-w-[320px]">
            <div className="flex flex-col gap-3 sm:gap-4">
              <Slider
                id={setting.key}
                value={[numValue]}
                min={sliderMin}
                max={sliderMax}
                step={sliderStep}
                onValueChange={(vals) => onChange(setting.key, vals[0].toString())}
                disabled={saving}
              />
              <Input
                type="number"
                value={currentValue}
                onChange={(e) => onChange(setting.key, e.target.value)}
                min={sliderMin}
                max={sliderMax}
                step={sliderStep}
                disabled={saving}
                className="w-full sm:w-24"
              />
            </div>
          </div>
        </div>
      );
    }
    case "password":
      return (
        <div className="flex flex-col gap-4 py-4 sm:flex-row sm:items-start sm:gap-6">
          <div className="space-y-1 sm:flex-1">
            <Label htmlFor={setting.key} className="flex items-center gap-1.5 text-sm font-medium">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="h-3.5 w-3.5 cursor-help text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="border-border bg-popover text-popover-foreground">
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">{setting.description}</p>
          </div>
          <div className="w-full sm:min-w-[220px] sm:max-w-[280px]">
            <Input
              id={setting.key}
              type="password"
              value={currentValue}
              onChange={(e) => onChange(setting.key, e.target.value)}
              disabled={saving}
              autoComplete="off"
            />
          </div>
        </div>
      );
    default:
      return (
        <div className="flex flex-col gap-4 py-4 sm:flex-row sm:items-start sm:gap-6">
          <div className="space-y-1 sm:flex-1">
            <Label htmlFor={setting.key} className="flex items-center gap-1.5 text-sm font-medium">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="h-3.5 w-3.5 cursor-help text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8} className="border-border bg-popover text-popover-foreground">
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">{setting.description}</p>
          </div>
          <div className="w-full sm:min-w-[220px] sm:max-w-[280px]">
            <Input
              id={setting.key}
              type="text"
              value={currentValue}
              onChange={(e) => onChange(setting.key, e.target.value)}
              disabled={saving}
            />
          </div>
        </div>
      );
  }
}
