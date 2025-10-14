"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { UserCircle, SlidersHorizontal, Database, Info } from "lucide-react";

const itemClasses =
  "flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors focus:bg-secondary focus:text-secondary-foreground";

interface NavUserProps {
  collapsed?: boolean;
}

export function NavUser({ collapsed = false }: NavUserProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const maintenanceActive = pathname.startsWith("/maintenance");
  const aboutActive = pathname.startsWith("/about");
  const dropdownActive = maintenanceActive || aboutActive;
  const section = searchParams.get("section") === "data" ? "data" : "configuration";

  const navigate = (target: "configuration" | "data") => {
    const params = new URLSearchParams();
    params.set("section", target);
    router.push(`/maintenance?${params.toString()}`);
  };

  const maintenanceItems = [
    {
      key: "configuration",
      label: "Configuration",
      icon: SlidersHorizontal,
      isActive: maintenanceActive && section === "configuration",
      action: () => navigate("configuration"),
    },
    {
      key: "data",
      label: "Maintenance",
      icon: Database,
      isActive: maintenanceActive && section === "data",
      action: () => navigate("data"),
    },
  ] as const;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open maintenance menu"
          className={cn(
            "rounded-full border bg-card text-muted-foreground shadow-sm transition-colors",
            collapsed ? "h-10 w-10" : "h-11 w-11 sm:h-12 sm:w-12",
            dropdownActive ? "bg-primary/10 text-primary" : "hover:bg-secondary hover:text-secondary-foreground"
          )}
        >
          <span className="flex h-full w-full items-center justify-center rounded-full">
            <UserCircle className={cn("h-6 w-6", collapsed && "h-5 w-5")} />
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        sideOffset={12}
        className="w-56 rounded-xl border bg-card/95 p-2 shadow-lg backdrop-blur"
      >
        <DropdownMenuLabel className="px-3 pt-1 text-xs font-semibold uppercase text-muted-foreground">
          Workspace
        </DropdownMenuLabel>

        {maintenanceItems.map((item) => (
          <DropdownMenuItem
            key={item.key}
            onSelect={(event) => {
              event.preventDefault();
              item.action();
            }}
            className={cn(itemClasses, item.isActive && "bg-secondary text-secondary-foreground font-semibold")}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </DropdownMenuItem>
        ))}

        <DropdownMenuSeparator className="my-1" />

        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            router.push("/about");
          }}
          className={cn(itemClasses, aboutActive && "bg-secondary text-secondary-foreground font-semibold")}
        >
          <Info className="h-4 w-4" />
          About Snappy
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
