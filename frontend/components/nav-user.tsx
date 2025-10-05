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

export function NavUser() {
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

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open maintenance menu"
          className={cn(
            "h-9 w-9 sm:h-10 sm:w-10 rounded-full border transition-colors",
            dropdownActive ? "bg-blue-600 text-white shadow border-blue-500" : "border-transparent hover:border-blue-200/60 hover:bg-blue-50"
          )}
        >
          <UserCircle className={cn("h-5 w-5", dropdownActive ? "text-white" : "text-blue-600")} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuLabel className="text-muted-foreground text-xs uppercase tracking-[0.3em]">System</DropdownMenuLabel>
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            navigate("configuration");
          }}
          className={cn(
            "flex items-center gap-2",
            maintenanceActive && section === "configuration" && "font-medium text-blue-600 bg-blue-50/80"
          )}
        >
          <SlidersHorizontal className="h-4 w-4" />
          Configuration
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            navigate("data");
          }}
          className={cn(
            "flex items-center gap-2",
            maintenanceActive && section === "data" && "font-medium text-blue-600 bg-blue-50/80"
          )}
        >
          <Database className="h-4 w-4" />
          Data Management
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            router.push("/about");
          }}
          className={cn("flex items-center gap-2", aboutActive && "font-medium text-blue-600 bg-blue-50/80")}
        >
          <Info className="h-4 w-4" />
          About
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
