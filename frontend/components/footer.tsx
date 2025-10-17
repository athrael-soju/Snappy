import Image from "next/image";
import Link from "next/link";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const techStack = [
  {
    name: "FastAPI",
    href: "https://fastapi.tiangolo.com",
    lightSrc: "/logos/FastAPI.svg",
    darkSrc: "/logos/FastAPI.svg",
    description: "Lightning-fast Python backend for the API layer.",
  },
  {
    name: "Next.js",
    href: "https://nextjs.org",
    lightSrc: "/logos/nextjs-icon-light-background.svg",
    darkSrc: "/logos/nextjs-icon-dark-background.svg",
    description: "React framework powering the dynamic frontend.",
  },
  {
    name: "Qdrant",
    href: "https://qdrant.tech",
    lightSrc: "/logos/Qdrant.svg",
    darkSrc: "/logos/Qdrant.svg",
    description: "Vector database keeping visual embeddings searchable.",
  },
  {
    name: "Illuin Tech - ColPali",
    href: "https://github.com/illuin-tech/colpali",
    lightSrc: "/logos/Illuin-Tech-Colpali.png",
    darkSrc: "/logos/Illuin-Tech-Colpali.png",
    description: "ColPali: State-of-the-art vision model for document understanding.",
  },
] as const;

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative shrink-0 border-t border-border/40 bg-background/50 backdrop-blur-xl">
      {/* Subtle gradient line at bottom */}
      <div className="absolute inset-x-0 bottom-0 h-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />

      <div className="container mx-auto px-4 py-2 sm:py-3">
        <div className="flex flex-col items-center justify-between gap-2 sm:flex-row sm:gap-4">
          <p className="text-center text-body-xs text-muted-foreground sm:text-left sm:text-body-sm">
            (c) {currentYear}{" "}
            <span className="bg-gradient-to-r from-primary to-chart-4 bg-clip-text font-bold text-transparent">
              Snappy!
            </span>{" "}
            Crafted for lightning-fast visual retrieval.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-body-xs text-muted-foreground sm:gap-x-3 sm:text-body-sm">
            <span>Powered by</span>
            <TooltipProvider delayDuration={100}>
              <div className="flex items-center gap-2 sm:gap-3">
                {techStack.map((tech) => (
                  <Tooltip key={tech.name}>
                    <TooltipTrigger asChild>
                      <Link
                        href={tech.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="transition-transform hover:scale-105"
                        aria-label={tech.name}
                      >
                        <Image
                          src={tech.lightSrc}
                          alt={`${tech.name} logo`}
                          width={32}
                          height={32}
                          className={`h-5 w-auto sm:h-6${tech.darkSrc !== tech.lightSrc ? " dark:hidden" : ""}`}
                        />
                        {tech.darkSrc !== tech.lightSrc && (
                          <Image
                            src={tech.darkSrc}
                            alt={`${tech.name} logo`}
                            width={32}
                            height={32}
                            className="hidden h-5 w-auto sm:h-6 dark:block"
                          />
                        )}
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-[220px]">
                      <p className="text-xs font-semibold leading-tight text-background">
                        {tech.name}
                      </p>
                      <p className="text-[11px] leading-tight text-background/80">
                        {tech.description}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                ))}
              </div>
            </TooltipProvider>
          </div>
        </div>
      </div>
    </footer>
  );
}
