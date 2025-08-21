import * as React from "react";
import { cn } from "@/lib/utils";

export type SpinnerProps = React.HTMLAttributes<HTMLDivElement> & {
  size?: number;
};

export const Spinner = ({ className, size = 20, ...props }: SpinnerProps) => {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading"
      className={cn("inline-flex items-center", className)}
      {...props}
    >
      <svg
        className="animate-spin text-black/70 dark:text-white/70"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          d="M4 12a8 8 0 018-8"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
};
