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
    router.push("/maintenance?" + params.toString());
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Open maintenance menu"
          className={cn(
            "group relative h-11 w-11 sm:h-12 sm:w-12 rounded-full border-none bg-gradient-to-br from-pink-400 via-purple-400 to-sky-400 p-[2px] shadow-sm transition-all",
            dropdownActive ? "shadow-lg" : "hover:shadow-md"
          )}
        >
          <span
            className={cn(
              "flex h-full w-full items-center justify-center rounded-full bg-white/95 text-pink-500 transition-all",
              dropdownActive && "bg-gradient-to-br from-blue-600 via-purple-600 to-cyan-500 text-white"
            )}
          >
            <UserCircle className="h-6 w-6" />
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={12} className="w-56 rounded-2xl border border-pink-200/60 bg-white/95 shadow-xl">
        <DropdownMenuLabel className="px-3 pt-2 text-[11px] font-semibold uppercase tracking-[0.35em] text-pink-500">System</DropdownMenuLabel>
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            navigate("configuration");
          }}
          className={cn(
            "mx-1 flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition",
            maintenanceActive && section === "configuration"
              ? "bg-pink-100/80 text-pink-600 font-semibold"
              : "hover:bg-pink-50"
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
            "mx-1 flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition",
            maintenanceActive && section === "data"
              ? "bg-pink-100/80 text-pink-600 font-semibold"
              : "hover:bg-pink-50"
          )}
        >
          <Database className="h-4 w-4" />
          Data Management
        </DropdownMenuItem>
        <DropdownMenuSeparator className="my-2" />
        <DropdownMenuItem
          onSelect={(event) => {
            event.preventDefault();
            router.push("/about");
          }}
          className={cn(
            "mx-1 mb-1 flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition",
            aboutActive ? "bg-pink-100/80 text-pink-600 font-semibold" : "hover:bg-pink-50"
          )}
        >
          <Info className="h-4 w-4" />
          About
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
