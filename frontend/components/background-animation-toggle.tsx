"use client";

import { useCallback } from "react";
import { Switch } from "@/components/ui/switch";
import { useAppStore } from "@/stores/app-store";

type BackgroundAnimationToggleProps = Omit<
  React.ComponentProps<typeof Switch>,
  "checked" | "defaultChecked" | "onCheckedChange"
>;

export function BackgroundAnimationToggle({ id, className, ...rest }: BackgroundAnimationToggleProps) {
  const { state, dispatch } = useAppStore();
  const enabled = state.preferences.animatedBackground;

  const handleChange = useCallback(
    (checked: boolean) => {
      dispatch({ type: "SET_ANIMATED_BACKGROUND", payload: checked });
    },
    [dispatch],
  );

  return (
    <Switch
      id={id}
      className={className}
      checked={enabled}
      onCheckedChange={handleChange}
      aria-label="Toggle animated background"
      {...rest}
    />
  );
}
