import Image from "next/image";
import Link from "next/link";

import { AppButton } from "@/components/app-button";
import { InfoTooltip } from "@/components/info-tooltip";

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
    <footer className="relative shrink-0 border-t border-vultr-blue-60/40 bg-vultr-midnight text-white">
      <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-vultr-blue via-vultr-light-blue to-vultr-blue-60" />
      <div className="mx-auto max-w-7xl px-4 py-4 md:px-6">
        <div className=" flex flex-col gap-3 border-white/15 text-xs text-white/60 md:flex-row md:items-center md:justify-between">
          <p>© {currentYear} Vultr Holdings Corporation. All rights reserved.</p>
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <p className="text-xs uppercase tracking-[0.18em] text-white/70">Powered By</p>
            {techStack.map((tech) => (
              <InfoTooltip
                key={tech.name}
                trigger={
                  <Link
                    href={tech.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs text-white/80 transition hover:bg-white/20"
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
                    {/* <span>{tech.name}</span> */}
                  </Link>
                }
                title={tech.name}
                description={tech.description}
                side="top"
                contentClassName="max-w-[220px]"
              />
            ))}
          </div>
          <div className="flex flex-wrap gap-4">
            <Link
              href="https://www.vultr.com/legal/privacy/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition hover:text-white"
            >
              Privacy
            </Link>
            <Link
              href="https://www.vultr.com/legal/tos/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition hover:text-white"
            >
              Terms
            </Link>
            <Link
              href="https://www.vultr.com/company/accessibility/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition hover:text-white"
            >
              Accessibility
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
