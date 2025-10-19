/* eslint-disable react/no-array-index-key */
"use client";

import React, { useMemo, useState } from 'react';
import { AppButton } from '@/components/app-button';
import { Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import CitationHoverCard from './CitationHoverCard';

type ImageData = {
  url: string | null;
  label: string | null;
  score: number | null;
};

type MarkdownRendererProps = {
  content: string;
  images?: ImageData[];
  onImageClick?: (url: string, label?: string) => void;
  className?: string;
};

// Inline helper to render fenced code blocks with copy functionality
function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="relative group my-4">
      <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <AppButton
          variant="ghost"
          size="xs"
          onClick={handleCopy}
          elevated
        >
          {copied ? (
            <>
              <Check className="mr-1 size-icon-2xs text-green-500" />
              <span className="text-body-xs">Copied</span>
            </>
          ) : (
            <>
              <Copy className="mr-1 size-icon-2xs" />
              <span className="text-body-xs">Copy</span>
            </>
          )}
        </AppButton>
      </div>
      <pre className="max-w-full overflow-x-auto rounded-lg border bg-muted/50 p-4">
        {language && (
          <div className="mb-2 text-body-xs font-medium text-muted-foreground">{language}</div>
        )}
        <code className="block font-mono text-body-sm text-foreground">{code}</code>
      </pre>
    </div>
  );
}

/**
 * Lightweight markdown renderer tuned for assistant responses.
 * Supports headings, lists, inline formatting, fenced code, and in-text citations.
 */
export default function MarkdownRenderer({
  content,
  images = [],
  onImageClick,
  className,
}: MarkdownRendererProps) {
  const citationMap = useMemo(() => {
    const map = new Map<string, { number: number; image: ImageData }>();
    let citationNumber = 1;
    const citationRegex =
      /\(([^)]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^)]*)\)|\[([^\]]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^\]]*)\]/g;
    const matches = content.matchAll(citationRegex);

    for (const match of matches) {
      const citation = match[1] || match[2];
      if (!citation) continue;
      const normalized = citation.toLowerCase().trim();
      if (map.has(normalized)) continue;
      const image = images.find(
        (img) => img.label && citation.toLowerCase().includes(img.label.toLowerCase()),
      );
      if (image && image.url) {
        map.set(normalized, { number: citationNumber++, image });
      }
    }

    return map;
  }, [content, images]);

  const getCitationInfo = (citation: string) => {
    const normalized = citation.toLowerCase().trim();
    return citationMap.get(normalized);
  };

  const processTextFormatting = (text: string, baseKey: number): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let keyCounter = 0;

    while (remaining.length > 0) {
      const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
      if (boldMatch && boldMatch.index !== undefined) {
        if (boldMatch.index > 0) {
          parts.push(remaining.slice(0, boldMatch.index));
        }
        parts.push(
          <strong key={`${baseKey}-bold-${keyCounter++}`} className="font-semibold text-foreground">
            {boldMatch[1]}
          </strong>,
        );
        remaining = remaining.slice(boldMatch.index + boldMatch[0].length);
        continue;
      }

      const italicMatch = remaining.match(/(?<!\*)\*([^*]+)\*(?!\*)/);
      if (italicMatch && italicMatch.index !== undefined) {
        if (italicMatch.index > 0) {
          parts.push(remaining.slice(0, italicMatch.index));
        }
        parts.push(
          <em key={`${baseKey}-italic-${keyCounter++}`} className="italic">
            {italicMatch[1]}
          </em>,
        );
        remaining = remaining.slice(italicMatch.index + italicMatch[0].length);
        continue;
      }

      const codeMatch = remaining.match(/`([^`]+)`/);
      if (codeMatch && codeMatch.index !== undefined) {
        if (codeMatch.index > 0) {
          parts.push(remaining.slice(0, codeMatch.index));
        }
        parts.push(
          <code
            key={`${baseKey}-code-${keyCounter++}`}
            className="rounded border bg-muted px-1.5 py-0.5 font-mono text-body-sm"
          >
            {codeMatch[1]}
          </code>,
        );
        remaining = remaining.slice(codeMatch.index + codeMatch[0].length);
        continue;
      }

      parts.push(remaining);
      break;
    }

    return parts;
  };

  const renderInlineFormatting = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let keyCounter = 0;
    let citationsInSentence = 0;
    const MAX_CITATIONS_PER_SENTENCE = 2;

    while (remaining.length > 0) {
      const sentenceEndMatch = remaining.match(/[.!?]\s/);
      if (sentenceEndMatch && sentenceEndMatch.index === 0) {
        citationsInSentence = 0;
      }

      const citationMatch =
        remaining.match(/\(([^)]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^)]*)\)|\[([^\]]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^\]]*)\]/);

      if (citationMatch) {
        const beforeCitation = remaining.slice(0, citationMatch.index);
        const citation = citationMatch[1] || citationMatch[2];

        if (beforeCitation) {
          parts.push(...processTextFormatting(beforeCitation, keyCounter++));
        }

        const citationInfo = citation ? getCitationInfo(citation) : null;
        if (citationInfo && citationsInSentence < MAX_CITATIONS_PER_SENTENCE) {
          citationsInSentence += 1;
          parts.push(
            <CitationHoverCard
              key={`cite-${keyCounter++}`}
              number={citationInfo.number}
              imageUrl={citationInfo.image.url!}
              label={citationInfo.image.label || citation}
              score={citationInfo.image.score}
              onOpen={() => {
                if (citationInfo.image.url) {
                  onImageClick?.(citationInfo.image.url, citationInfo.image.label || undefined);
                }
              }}
            />,
          );
        }
        remaining = remaining.slice(citationMatch.index! + citationMatch[0].length);
      } else {
        parts.push(...processTextFormatting(remaining, keyCounter++));
        break;
      }
    }

    return parts;
  };

  const renderContent = () => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let codeBlockLang = '';

    lines.forEach((line, idx) => {
      if (line.trim().startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockLang = line.trim().slice(3).trim();
          codeBlockContent = [];
        } else {
          elements.push(
            <CodeBlock key={`code-${idx}`} code={codeBlockContent.join('\n')} language={codeBlockLang} />,
          );
          inCodeBlock = false;
          codeBlockContent = [];
          codeBlockLang = '';
        }
        return;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        return;
      }

      if (!line.trim()) {
        elements.push(<div key={`space-${idx}`} className="h-3" />);
        return;
      }

      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={`h1-${idx}`} className="mt-6 mb-3 text-editorial-h3 font-semibold text-balance">
            {renderInlineFormatting(line.slice(2))}
          </h1>,
        );
        return;
      }
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={`h2-${idx}`} className="mt-5 mb-2 text-editorial-h4 font-semibold text-balance">
            {renderInlineFormatting(line.slice(3))}
          </h2>,
        );
        return;
      }
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={`h3-${idx}`} className="mt-4 mb-2 text-editorial-h5 font-semibold text-balance">
            {renderInlineFormatting(line.slice(4))}
          </h3>,
        );
        return;
      }

      if (line.trim().match(/^[-*]\s/)) {
        elements.push(
          <div key={`li-${idx}`} className="my-1 ml-4 flex gap-2">
            <span className="font-bold text-purple-500">•</span>
            <span className="flex-1">{renderInlineFormatting(line.trim().slice(2))}</span>
          </div>,
        );
        return;
      }

      const orderedListMatch = line.trim().match(/^(\d+)\.\s(.*)$/);
      if (orderedListMatch) {
        elements.push(
          <div key={`ol-${idx}`} className="my-1 ml-4 flex gap-2">
            <span className="font-semibold text-purple-500">{orderedListMatch[1]}.</span>
            <span className="flex-1">{renderInlineFormatting(orderedListMatch[2])}</span>
          </div>,
        );
        return;
      }

      elements.push(
        <p key={`p-${idx}`} className="my-2 text-body-sm leading-relaxed">
          {renderInlineFormatting(line)}
        </p>,
      );
    });

    return elements;
  };

  return (
    <div
      className={cn(
        'max-w-none space-y-3 text-body-sm leading-relaxed text-foreground sm:text-body',
        className,
      )}
    >
      {renderContent()}
    </div>
  );
}
