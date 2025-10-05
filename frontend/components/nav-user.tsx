"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { UserCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function NavUser() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const maintenanceActive = pathname.startsWith("/maintenance");
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
            "h-9 w-9 sm:h-10 sm:w-10 rounded-full border border-transparent transition-colors",
            maintenanceActive ? "bg-blue-600 text-white shadow" : "hover:border-blue-200/60 hover:bg-blue-50"
          )}
        >
          <UserCircle className={cn("h-5 w-5", maintenanceActive ? "text-white" : "text-blue-600") } />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            navigate("configuration");
          }}
          className={section === "configuration" ? "font-medium text-blue-600" : ""}
        >
          Configuration
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            navigate("data");
          }}
          className={section === "data" ? "font-medium text-blue-600" : ""}
        >
          Data Management
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
