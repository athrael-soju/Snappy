"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/8bit/avatar";
import { Badge } from "@/components/ui/8bit/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/8bit/card";
import { Button } from "@/components/ui/8bit/button";

function getInitials(name: string) {
  if (!name) return "?";
  const parts = name.trim().split(/s+/);
  const initials = parts.slice(0, 2).map((p) => p[0]?.toUpperCase()).join("");
  return initials || "?";
}

export default function ProfileCard() {
  return (
    <Card className="min-w-sm max-w-md">
      <CardHeader className="flex flex-col items-center gap-2">
         <Avatar className="size-20" variant="retro">
          <AvatarImage src="/avatar.jpg" alt="Athrael Soju" />
          <AvatarFallback>{getInitials("Athrael Soju")}</AvatarFallback>
        </Avatar>

        <CardTitle>
          <h3>Athrael Soju</h3>
        </CardTitle>

        <Badge>Spicy</Badge>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4">
        
        <p className="text-sm text-muted-foreground text-center w-3/4 mx-auto">
          Life's too short for 
        </p>
        
        <div className="flex items-center gap-4 justify-center">
          <div className="flex items-center gap-3 text-sm">
            
              <Button size="icon" asChild>
                <a href="https://github.com/athrael-soju" target="_blank" rel="noreferrer" className="inline-flex items-center justify-center size-8 px-0">
                {/* Github icon */}
                 <svg
                    width="50"
                    height="50"
                    viewBox="0 0 256 256"
                    fill="currentColor"
                    xmlns="http://www.w3.org/2000/svg"
                    stroke="currentColor"
                    strokeWidth="0.25"
                    aria-label="github"
                    className="size-7"
                  >
                    <rect x="200" y="80" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="64" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="96" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="48" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="48" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="64" width="14" height="14" rx="1"></rect>
                    <rect x="88" y="48" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="48" width="14" height="14" rx="1"></rect>
                    <rect x="104" y="48" width="14" height="14" rx="1"></rect>
                    <rect x="136" y="48" width="14" height="14" rx="1"></rect>
                    <rect x="120" y="48" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="64" width="14" height="14" rx="1"></rect>
                    <rect x="104" y="64" width="14" height="14" rx="1"></rect>
                    <rect x="136" y="64" width="14" height="14" rx="1"></rect>
                    <rect x="120" y="64" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="64" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="80" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="96" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="112" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="128" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="80" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="96" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="112" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="128" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="80" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="96" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="112" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="80" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="80" width="14" height="14" rx="1"></rect>
                    <rect x="88" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="128" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="136" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="104" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="128" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="128" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="160" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="160" width="14" height="14" rx="1"></rect>
                    <rect x="88" y="192" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="176" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="176" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="160" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="160" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="176" width="14" height="14" rx="1"></rect>
                    <rect x="88" y="176" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="192" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="192" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="192" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="176" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="176" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="160" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="160" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="128" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="144" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="112" width="14" height="14" rx="1"></rect>
                  </svg>
              </a>
              </Button>
            <span className="text-muted-foreground">•</span>
            
              <Button size="icon" asChild>
                <a href="https://www.youtube.com/shorts/Ay8lynMZ4mE" target="_blank" rel="noreferrer" className="inline-flex items-center justify-center size-8 px-0">
                {/* Twitter icon */}
                <svg
                    width="50"
                    height="50"
                    viewBox="0 0 256 256"
                    fill="currentColor"
                    xmlns="http://www.w3.org/2000/svg"
                    stroke="currentColor"
                    strokeWidth="0.25"
                    aria-label="twitter"
                    className="size-6"
                  >
                    <rect x="40" y="40" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="40" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="56" width="14" height="14" rx="1"></rect>
                    <rect x="88" y="72" width="14" height="14" rx="1"></rect>
                    <rect x="104" y="88" width="14" height="14" rx="1"></rect>
                    <rect x="120" y="104" width="14" height="14" rx="1"></rect>
                    <rect x="136" y="120" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="136" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="152" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="184" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="200" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="200" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="168" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="184" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="168" width="14" height="14" rx="1"></rect>
                    <rect x="136" y="152" width="14" height="14" rx="1"></rect>
                    <rect x="120" y="136" width="14" height="14" rx="1"></rect>
                    <rect x="104" y="120" width="14" height="14" rx="1"></rect>
                    <rect x="88" y="104" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="88" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="72" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="56" width="14" height="14" rx="1"></rect>
                    <rect x="136" y="104" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="88" width="14" height="14" rx="1"></rect>
                    <rect x="200" y="40" width="14" height="14" rx="1"></rect>
                    <rect x="40" y="200" width="14" height="14" rx="1"></rect>
                    <rect x="152" y="88" width="14" height="14" rx="1"></rect>
                    <rect x="168" y="72" width="14" height="14" rx="1"></rect>
                    <rect x="184" y="56" width="14" height="14" rx="1"></rect>
                    <rect x="104" y="136" width="14" height="14" rx="1"></rect>
                    <rect x="88" y="152" width="14" height="14" rx="1"></rect>
                    <rect x="72" y="168" width="14" height="14" rx="1"></rect>
                    <rect x="56" y="184" width="14" height="14" rx="1"></rect>
                  </svg>
              </a>
              </Button>
          </div>
        </div>
      </CardContent>
      <CardFooter className="justify-end gap-2"></CardFooter>
    </Card>
  );
}