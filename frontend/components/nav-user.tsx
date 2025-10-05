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
            "group transition-transform hover:scale-105 h-9 w-9 sm:h-10 sm:w-10 border border-transparent hover:border-blue-200/50",
            maintenanceActive && "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
          )}
        >
          <UserCircle
            className={cn(
              "w-5 h-5 sm:w-5 sm:h-5 transition-colors duration-300",
              maintenanceActive ? "text-white" : "text-blue-600 group-hover:text-cyan-600"
            )}
          />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            navigate("configuration");
          }}
          className={section === "configuration" ? "font-semibold" : ""}
        >
          Configuration
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            navigate("data");
          }}
          className={section === "data" ? "font-semibold" : ""}
        >
          Data Management
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
