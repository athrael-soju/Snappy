import Image from "next/image";
import Link from "next/link";

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

type FooterLink = {
  label: string;
  href: string;
  external?: boolean;
};

type FooterColumn = {
  title: string;
  links: FooterLink[];
};

const footerColumns: FooterColumn[] = [
  {
    title: "Services",
    links: [
      { label: "Upload & Index", href: "/upload" },
      { label: "Semantic Search", href: "/search" },
      { label: "Vision Chat", href: "/chat" },
    ],
  },
  {
    title: "Management",
    links: [
      { label: "Maintenance", href: "/maintenance" },
      { label: "Configuration", href: "/configuration" },
      { label: "Docs", href: "/about" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Brand Book", href: "/vultr/vultr-brand-book.pdf", external: true },
      { label: "Support Center", href: "https://www.vultr.com/support/", external: true },

    ],
  },
  {
    title: "Company",
    links: [
      { label: "About Vultr", href: "https://www.vultr.com/company/about/", external: true },
      { label: "Careers", href: "https://www.vultr.com/company/careers/", external: true },
      { label: "Press", href: "https://www.vultr.com/company/press/", external: true },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "https://www.vultr.com/legal/privacy/", external: true },
      { label: "Terms of Service", href: "https://www.vultr.com/legal/tos/", external: true },
      { label: "Security", href: "https://www.vultr.com/company/security/", external: true },
    ],
  },
];

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-black/5 bg-white text-vultr-navy dark:border-white/10 dark:bg-vultr-midnight/95 dark:text-white">
      <div className="layout-container max-w-7xl py-12 md:py-16">
        <div className="grid gap-10 lg:grid-cols-[1.2fr,3fr]">
          <div className="space-y-6">
            <Link href="/" className="inline-flex items-center" aria-label="Vultr home">
              <Image
                src="/brand/vultr-logo.svg"
                alt="Vultr"
                width={140}
                height={42}
                className="h-9 w-auto dark:invert"
              />
            </Link>
            <p className="max-w-sm text-body-sm text-vultr-navy/70 dark:text-white/70">
              Deploy Vultr&rsquo;s ColPali-powered document intelligence with brand-correct surfaces, global
              infrastructure, and enterprise-grade controls.
            </p>
            <div className="space-y-3">
              <p className="eyebrow text-vultr-navy/60 dark:text-white/60">
                Powered By
              </p>
              <div className="flex flex-wrap gap-3">
                {techStack.map((tech) => (
                  <InfoTooltip
                    key={tech.name}
                    trigger={
                      <Link
                        href={tech.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 rounded-[var(--radius-button)] border border-black/10 bg-white px-3 py-1.5 text-body-xs text-vultr-navy/70 transition hover:border-vultr-blue/30 hover:text-vultr-blue dark:border-white/15 dark:bg-vultr-midnight/70 dark:text-white/70 dark:hover:border-vultr-light-blue/30 dark:hover:text-white"
                        aria-label={tech.name}
                      >
                        <Image
                          src={tech.lightSrc}
                          alt={`${tech.name} logo`}
                          width={28}
                          height={28}
                          className={`h-5 w-auto${tech.darkSrc !== tech.lightSrc ? " dark:hidden" : ""}`}
                        />
                        {tech.darkSrc !== tech.lightSrc && (
                          <Image
                            src={tech.darkSrc}
                            alt={`${tech.name} logo`}
                            width={28}
                            height={28}
                            className="hidden h-5 w-auto dark:block"
                          />
                        )}
                      </Link>
                    }
                    title={tech.name}
                    description={tech.description}
                    side="top"
                    contentClassName="max-w-[220px]"
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5">
            {footerColumns.map((column) => (
              <div key={column.title} className="space-y-4">
                <p className="eyebrow text-vultr-navy/60 dark:text-white/60">
                  {column.title}
                </p>
                <ul className="space-y-3 text-body-sm">
                  {column.links.map((link) => (
                    <li key={`${column.title}-${link.label}`}>
                      <Link
                        href={link.href}
                        target={link.external ? "_blank" : undefined}
                        rel={link.external ? "noopener noreferrer" : undefined}
                        className="text-vultr-navy/80 transition hover:text-vultr-blue dark:text-white/70 dark:hover:text-vultr-light-blue"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-black/5 bg-white/80 py-4 dark:border-white/10 dark:bg-vultr-midnight/85">
        <div className="layout-container max-w-7xl flex flex-col gap-3 text-body-xs text-vultr-navy/60 dark:text-white/60 md:flex-row md:items-center md:justify-between">
          <p>&copy; {currentYear} Vultr Holdings Corporation. All rights reserved.</p>
          <div className="flex flex-wrap gap-x-4 gap-y-2">
            <Link
              href="https://www.vultr.com/legal/privacy/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition hover:text-vultr-blue dark:hover:text-vultr-light-blue"
            >
              Privacy
            </Link>
            <Link
              href="https://www.vultr.com/legal/tos/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition hover:text-vultr-blue dark:hover:text-vultr-light-blue"
            >
              Terms
            </Link>
            <Link
              href="https://www.vultr.com/company/accessibility/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition hover:text-vultr-blue dark:hover:text-vultr-light-blue"
            >
              Accessibility
            </Link>
            <Link
              href="https://www.vultr.com/company/security/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition hover:text-vultr-blue dark:hover:text-vultr-light-blue"
            >
              Security
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
