"use client";

import "@/lib/api/client";
import { useConfigurationPanel } from "@/lib/hooks/use-configuration-panel";

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
  } = useConfigurationPanel();

  if (loading && !schema) {
    return (
      <main className="mx-auto max-w-4xl p-4">
        <p className="text-sm text-muted-foreground">Loading configuration...</p>
      </main>
    );
  }

  if (!schema) {
    return (
      <main className="mx-auto max-w-4xl p-4">
        <h1 className="text-2xl font-semibold text-foreground">Configuration</h1>
        <p className="mt-3 text-sm text-muted-foreground">
          Configuration data could not be loaded. Check that the API is reachable.
        </p>
      </main>
    );
  }

  const categories = Object.entries(schema).sort(([, a], [, b]) => a.order - b.order);
  const activeCategory = categories.find(([key]) => key === activeTab) ?? categories[0];
  const activeKey = activeCategory?.[0] ?? activeTab;
  const activeContent = activeCategory?.[1];

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">Configuration</h1>
        <p className="text-sm text-muted-foreground">
          Edit backend settings directly. Inputs mirror the OpenAPI schema and save values one by one.
        </p>
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      </header>

      <section className="space-y-3 rounded border border-border p-4 text-sm">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2">
            <span className="font-medium text-foreground">Category</span>
            <select
              value={activeKey}
              onChange={(event) => setActiveTab(event.target.value)}
              className="rounded border border-border px-3 py-2"
            >
              {categories.map(([key, category]) => (
                <option key={key} value={key}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            onClick={optimizeForSystem}
            className="rounded border border-border px-3 py-2 font-medium text-foreground disabled:opacity-50"
            disabled={saving}
          >
            Optimize for system
          </button>
          <button
            type="button"
            onClick={resetToDefaults}
            className="rounded border border-border px-3 py-2 font-medium text-foreground disabled:opacity-50"
            disabled={saving}
          >
            Reset all to defaults
          </button>
        </div>
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          <span>Total settings: {configStats.totalSettings}</span>
          <span>Modified: {configStats.modifiedSettings}</span>
          <span>Mode: {configStats.currentMode}</span>
          {configStats.enabledFeatures.length > 0 && (
            <span>Enabled features: {configStats.enabledFeatures.join(", ")}</span>
          )}
          {lastSaved && <span>Last saved: {lastSaved.toLocaleString()}</span>}
        </div>
      </section>

      {activeContent && (
        <section className="space-y-4 rounded border border-border p-4 text-sm">
          <header className="space-y-1">
            <h2 className="text-base font-semibold text-foreground">{activeContent.name}</h2>
            <p className="text-xs text-muted-foreground">{activeContent.description}</p>
          </header>

          <div className="space-y-4">
            {activeContent.settings
              .filter((setting) => isSettingVisible(setting))
              .map((setting) => {
                const currentValue = values[setting.key] ?? setting.default;

                if (setting.type === "boolean") {
                  return (
                    <article key={setting.key} className="space-y-2 rounded border border-dashed border-border p-3">
                      <label className="flex items-center gap-2 font-medium text-foreground">
                        <input
                          type="checkbox"
                          checked={(currentValue || "").toLowerCase() === "true"}
                          onChange={(event) => handleValueChange(setting.key, event.target.checked ? "True" : "False")}
                          disabled={saving}
                        />
                        {setting.label}
                      </label>
                      <p className="text-xs text-muted-foreground">{setting.description}</p>
                      {setting.help_text && <p className="text-xs text-muted-foreground">Hint: {setting.help_text}</p>}
                    </article>
                  );
                }

                if (setting.type === "select" && Array.isArray(setting.options)) {
                  return (
                    <article key={setting.key} className="space-y-2 rounded border border-dashed border-border p-3">
                      <label className="flex flex-col gap-1 font-medium text-foreground">
                        {setting.label}
                        <select
                          value={currentValue}
                          onChange={(event) => handleValueChange(setting.key, event.target.value)}
                          disabled={saving}
                          className="rounded border border-border px-3 py-2 text-sm"
                        >
                          {setting.options.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                      <p className="text-xs text-muted-foreground">{setting.description}</p>
                      {setting.help_text && <p className="text-xs text-muted-foreground">Hint: {setting.help_text}</p>}
                    </article>
                  );
                }

                const inputType = setting.type === "password" ? "password" : setting.type === "number" ? "number" : "text";
                const min = typeof setting.min === "number" ? setting.min : undefined;
                const max = typeof setting.max === "number" ? setting.max : undefined;
                const step = typeof setting.step === "number" ? setting.step : undefined;

                return (
                  <article key={setting.key} className="space-y-2 rounded border border-dashed border-border p-3">
                    <label className="flex flex-col gap-1 font-medium text-foreground">
                      {setting.label}
                      <input
                        type={inputType}
                        value={currentValue}
                        onChange={(event) => handleValueChange(setting.key, event.target.value)}
                        disabled={saving}
                        min={min}
                        max={max}
                        step={step}
                        className="rounded border border-border px-3 py-2 text-sm"
                      />
                    </label>
                    <p className="text-xs text-muted-foreground">{setting.description}</p>
                    {setting.help_text && <p className="text-xs text-muted-foreground">Hint: {setting.help_text}</p>}
                    {setting.depends_on && (
                      <p className="text-xs text-muted-foreground">
                        Visible when {setting.depends_on.key} is set to {setting.depends_on.value ? "True" : "False"}.
                      </p>
                    )}
                  </article>
                );
              })}
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => resetSection(activeKey)}
              className="rounded border border-border px-4 py-2 text-sm font-medium text-foreground disabled:opacity-50"
              disabled={saving}
            >
              Reset this section
            </button>
          </div>
        </section>
      )}

      <footer className="flex flex-wrap items-center gap-3 rounded border border-border p-4 text-sm">
        <button
          type="button"
          onClick={saveChanges}
          className="rounded bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50"
          disabled={!hasChanges || saving}
        >
          {saving ? "Saving..." : "Save changes"}
        </button>
        <button
          type="button"
          onClick={resetChanges}
          className="rounded border border-border px-4 py-2 font-medium text-foreground disabled:opacity-50"
          disabled={!hasChanges || saving}
        >
          Discard edits
        </button>
        {!hasChanges && <span className="text-xs text-muted-foreground">No unsaved changes.</span>}
      </footer>
    </main>
  );
}
