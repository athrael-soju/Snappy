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
                      <TooltipContent sideOffset={8}>
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
                    <TooltipContent sideOffset={8}>
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
                    <TooltipContent sideOffset={8}>
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
        <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
          <div className="space-y-0.5">
            <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8}>
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">{setting.description}</p>
          </div>
          <Select
            value={currentValue}
            onValueChange={(value) => onChange(setting.key, value)}
            disabled={saving}
          >
            <SelectTrigger id={setting.key}>
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
      );

    case "number":
      const numValue = parseFloat(currentValue) || parseFloat(setting.default);
      const min = setting.min ?? 0;
      const max = setting.max ?? 100;
      const step = setting.step ?? 1;

      return (
        <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
          <div className="space-y-0.5">
            <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8}>
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">
              {setting.description}
              {(min !== undefined || max !== undefined) && (
                <span className="ml-1 text-xs">
                  ({min}-{max})
                </span>
              )}
            </p>
          </div>
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
              className="w-20"
            />
          </div>
        </div>
      );

    case "password":
      return (
        <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
          <div className="space-y-0.5">
            <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8}>
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">{setting.description}</p>
          </div>
          <Input
            id={setting.key}
            type="password"
            value={currentValue}
            onChange={(e) => onChange(setting.key, e.target.value)}
            disabled={saving}
            autoComplete="off"
          />
        </div>
      );

    default: // text
      return (
        <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
          <div className="space-y-0.5">
            <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
              {setting.label}
              {setting.help_text && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent sideOffset={8}>
                      <p className="text-sm">{setting.help_text}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <p className="text-sm text-muted-foreground">{setting.description}</p>
          </div>
          <Input
            id={setting.key}
            type="text"
            value={currentValue}
            onChange={(e) => onChange(setting.key, e.target.value)}
            disabled={saving}
          />
        </div>
      );
  }
}

