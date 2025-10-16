"use client"

import "@/lib/api/client"

import { Page, PageSection } from "@/components/layout/page"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import {
  ButtonGroup,
  ButtonGroupSeparator,
} from "@/components/ui/button-group"
import { useConfigurationPanel } from "@/lib/hooks/use-configuration-panel"

const numberFormatter = new Intl.NumberFormat()

export default function ConfigurationPage() {
  const {
    schema,
    loading,
    saving,
    hasChanges,
    error,
    activeTab,
    setActiveTab,
    values,
    configStats,
    lastSaved,
    saveChanges,
    resetChanges,
    resetSection,
    resetToDefaults,
    optimizeForSystem,
    handleValueChange,
    isSettingVisible,
  } = useConfigurationPanel()

  if (loading && !schema) {
    return (
      <Page title="Configuration">
        <PageSection>
          <Card>
            <CardContent className="text-sm text-muted-foreground">
              Loading configuration...
            </CardContent>
          </Card>
        </PageSection>
      </Page>
    )
  }

  if (!schema) {
    return (
      <Page
        title="Configuration"
        description="Configuration data could not be loaded. Check that the API is reachable."
      >
        <PageSection>
          <Alert variant="destructive">
            <AlertTitle>Unavailable</AlertTitle>
            <AlertDescription>
              Configuration data could not be retrieved. Ensure the API is
              reachable and try again.
            </AlertDescription>
          </Alert>
        </PageSection>
      </Page>
    )
  }

  const categories = Object.entries(schema).sort(
    ([, a], [, b]) => a.order - b.order,
  )
  const activeCategory =
    categories.find(([key]) => key === activeTab) ?? categories[0]
  const activeKey = activeCategory?.[0] ?? activeTab
  const activeContent = activeCategory?.[1]

  const headerActions = (
    <div className="flex flex-wrap gap-2">
      <ButtonGroup>
        <Button
          onClick={saveChanges}
          disabled={!hasChanges || saving}
        >
          {saving ? "Saving..." : "Save changes"}
        </Button>
        <Button
          variant="outline"
          onClick={resetChanges}
          disabled={!hasChanges || saving}
        >
          Discard edits
        </Button>
      </ButtonGroup>

      <ButtonGroup>
        <Button
          variant="outline"
          onClick={optimizeForSystem}
          disabled={saving}
        >
          Optimize for system
        </Button>
        <ButtonGroupSeparator />
        <Button
          variant="outline"
          onClick={resetToDefaults}
          disabled={saving}
        >
          Reset all to defaults
        </Button>
      </ButtonGroup>
    </div>
  )

  return (
    <Page
      title="Configuration"
      description="Edit backend settings directly. Inputs mirror the OpenAPI schema and persist values individually."
      actions={headerActions}
    >
      {error && (
        <PageSection>
          <Alert variant="destructive">
            <AlertTitle>Configuration error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </PageSection>
      )}

      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>Configuration overview</CardTitle>
            <CardDescription>
              Pick a category to adjust specific settings and review current
              statistics.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            <div className="flex flex-wrap gap-4">
              <div className="flex flex-col gap-2">
                <Label htmlFor="configuration-category">Category</Label>
                <Select
                  value={activeKey}
                  onValueChange={(value) => setActiveTab(value)}
                >
                  <SelectTrigger id="configuration-category">
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map(([key, category]) => (
                      <SelectItem key={key} value={key}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-col gap-2">
                <Label>Status</Label>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">
                    Total {numberFormatter.format(configStats.totalSettings)}
                  </Badge>
                  <Badge variant="outline">
                    Modified {numberFormatter.format(configStats.modifiedSettings)}
                  </Badge>
                  <Badge variant="outline">Mode {configStats.currentMode}</Badge>
                </div>
              </div>
              {configStats.enabledFeatures.length > 0 && (
                <div className="flex flex-col gap-2">
                  <Label>Enabled features</Label>
                  <div className="flex flex-wrap gap-1 text-xs text-muted-foreground">
                    {configStats.enabledFeatures.map((feature) => (
                      <span key={feature} className="rounded-full bg-muted px-2 py-1">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {lastSaved && (
              <Badge variant="outline" className="w-fit">
                Last saved {lastSaved.toLocaleString()}
              </Badge>
            )}
          </CardContent>
        </Card>
      </PageSection>

      {activeContent && (
        <PageSection>
          <Card>
            <CardHeader className="gap-3">
              <CardTitle>{activeContent.name}</CardTitle>
              <CardDescription>{activeContent.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-(--space-section-stack)">
              {activeContent.settings
                .filter((setting) => isSettingVisible(setting))
                .map((setting) => {
                  const currentValue = values[setting.key] ?? setting.default

                  if (setting.type === "boolean") {
                    const checked = (currentValue || "").toLowerCase() === "true"
                    return (
                      <Card
                        key={setting.key}
                        className="border-border/40 shadow-none"
                      >
                        <CardContent className="flex flex-col gap-3">
                          <div className="flex items-start gap-3">
                            <Checkbox
                              id={setting.key}
                              checked={checked}
                              disabled={saving}
                              onCheckedChange={(checkedState) =>
                                handleValueChange(
                                  setting.key,
                                  checkedState ? "True" : "False",
                                )
                              }
                            />
                            <div className="flex flex-col gap-2">
                              <Label htmlFor={setting.key} className="text-base">
                                {setting.label}
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                {setting.description}
                              </p>
                              {setting.help_text && (
                                <p className="text-xs text-muted-foreground">
                                  Hint: {setting.help_text}
                                </p>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  }

                  if (setting.type === "select" && Array.isArray(setting.options)) {
                    return (
                      <Card
                        key={setting.key}
                        className="border-border/40 shadow-none"
                      >
                        <CardContent className="flex flex-col gap-3">
                          <Label htmlFor={setting.key} className="text-base">
                            {setting.label}
                          </Label>
                          <Select
                            value={currentValue}
                            onValueChange={(value) =>
                              handleValueChange(setting.key, value)
                            }
                            disabled={saving}
                          >
                            <SelectTrigger id={setting.key}>
                              <SelectValue placeholder="Choose an option" />
                            </SelectTrigger>
                            <SelectContent>
                              {setting.options.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <p className="text-xs text-muted-foreground">
                            {setting.description}
                          </p>
                          {setting.help_text && (
                            <p className="text-xs text-muted-foreground">
                              Hint: {setting.help_text}
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    )
                  }

                  const inputType =
                    setting.type === "password"
                      ? "password"
                      : setting.type === "number"
                        ? "number"
                        : "text"
                  const min =
                    typeof setting.min === "number" ? setting.min : undefined
                  const max =
                    typeof setting.max === "number" ? setting.max : undefined
                  const step =
                    typeof setting.step === "number" ? setting.step : undefined

                  return (
                    <Card
                      key={setting.key}
                      className="border-border/40 shadow-none"
                    >
                      <CardContent className="flex flex-col gap-3">
                        <Label htmlFor={setting.key} className="text-base">
                          {setting.label}
                        </Label>
                        <Input
                          id={setting.key}
                          type={inputType}
                          value={currentValue}
                          onChange={(event) =>
                            handleValueChange(setting.key, event.target.value)
                          }
                          disabled={saving}
                          min={min}
                          max={max}
                          step={step}
                        />
                        <p className="text-xs text-muted-foreground">
                          {setting.description}
                        </p>
                        {setting.help_text && (
                          <p className="text-xs text-muted-foreground">
                            Hint: {setting.help_text}
                          </p>
                        )}
                        {setting.depends_on && (
                          <p className="text-xs text-muted-foreground">
                            Visible when {setting.depends_on.key} is set to{" "}
                            {setting.depends_on.value ? "True" : "False"}.
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  )
                })}
            </CardContent>
            <CardFooter className="flex flex-wrap gap-3">
              <Button
                variant="outline"
                onClick={() => resetSection(activeKey)}
                disabled={saving}
              >
                Reset this section
              </Button>
            </CardFooter>
          </Card>
        </PageSection>
      )}
    </Page>
  )
}
