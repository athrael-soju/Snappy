"use client";

import React, { useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { FileText, ExternalLink, Copy, Check } from 'lucide-react';
import Image from 'next/image';
import CitationHoverCard from './CitationHoverCard';

interface ImageData {
  url: string | null;
  label: string | null;
  score: number | null;
}

interface MarkdownRendererProps {
  content: string;
  images?: ImageData[];
  onImageClick?: (url: string, label?: string) => void;
}

// Code block component with copy button
function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4">
      <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 px-2 bg-background/50 backdrop-blur-sm hover:bg-background/80"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 mr-1 text-green-500" />
              <span className="text-xs">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5 mr-1" />
              <span className="text-xs">Copy</span>
            </>
          )}
        </Button>
      </div>
      <pre className="bg-muted/50 rounded-lg p-4 overflow-x-auto border max-w-full">
        {language && (
          <div className="text-xs text-muted-foreground mb-2 font-medium">{language}</div>
        )}
        <code className="text-sm font-mono text-foreground block">
          {code}
        </code>
      </pre>
    </div>
  );
}

/**
 * Renders markdown-formatted text with numbered superscript citations.
 * Citations are deduplicated and numbered sequentially [1], [2], etc.
 * Max 2 citations per sentence.
 */
export default function MarkdownRenderer({ content, images = [], onImageClick }: MarkdownRendererProps) {
  // Build citation mapping: deduplicate by label and assign numbers
  const citationMap = useMemo(() => {
    const map = new Map<string, { number: number; image: ImageData }>();
    let citationNumber = 1;
    
    // Extract all citations from content
    const citationRegex = /\(([^)]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^)]*)\)|\[([^\]]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^\]]*)\]/g;
    const matches = content.matchAll(citationRegex);
    
    for (const match of matches) {
      const citation = match[1] || match[2];
      if (!citation) continue;
      
      // Normalize citation for deduplication
      const normalized = citation.toLowerCase().trim();
      
      if (!map.has(normalized)) {
        // Find matching image
        const image = images.find(img => 
          img.label && citation.toLowerCase().includes(img.label.toLowerCase())
        );
        
        if (image && image.url) {
          map.set(normalized, { number: citationNumber++, image });
        }
      }
    }
    
    return map;
  }, [content, images]);

  // Helper to find citation info
  const getCitationInfo = (citation: string) => {
    const normalized = citation.toLowerCase().trim();
    return citationMap.get(normalized);
  };
  const renderContent = () => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let codeBlockLang = '';

    lines.forEach((line, lineIdx) => {
      // Code block detection
      if (line.trim().startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockLang = line.trim().slice(3).trim();
          codeBlockContent = [];
        } else {
          // End code block
          elements.push(
            <CodeBlock
              key={`code-${lineIdx}`}
              code={codeBlockContent.join('\n')}
              language={codeBlockLang}
            />
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

      // Empty lines
      if (!line.trim()) {
        elements.push(<div key={`br-${lineIdx}`} className="h-3" />);
        return;
      }

      // Headers
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={`h1-${lineIdx}`} className="text-2xl font-bold mt-6 mb-3">
            {renderInlineFormatting(line.slice(2))}
          </h1>
        );
        return;
      }
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={`h2-${lineIdx}`} className="text-xl font-bold mt-5 mb-2">
            {renderInlineFormatting(line.slice(3))}
          </h2>
        );
        return;
      }
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={`h3-${lineIdx}`} className="text-lg font-semibold mt-4 mb-2">
            {renderInlineFormatting(line.slice(4))}
          </h3>
        );
        return;
      }

      // Lists
      if (line.trim().match(/^[-*]\s/)) {
        elements.push(
          <div key={`li-${lineIdx}`} className="flex gap-2 my-1 ml-4">
            <span className="text-purple-500 font-bold">•</span>
            <span className="flex-1">{renderInlineFormatting(line.trim().slice(2))}</span>
          </div>
        );
        return;
      }

      // Numbered lists
      if (line.trim().match(/^\d+\.\s/)) {
        const match = line.trim().match(/^(\d+)\.\s(.*)$/);
        if (match) {
          elements.push(
            <div key={`ol-${lineIdx}`} className="flex gap-2 my-1 ml-4">
              <span className="text-purple-500 font-semibold">{match[1]}.</span>
              <span className="flex-1">{renderInlineFormatting(match[2])}</span>
            </div>
          );
          return;
        }
      }

      // Regular paragraph
      elements.push(
        <p key={`p-${lineIdx}`} className="my-2 leading-7">
          {renderInlineFormatting(line)}
        </p>
      );
    });

    return elements;
  };

  const renderInlineFormatting = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let keyCounter = 0;
    let citationsInSentence = 0;
    const MAX_CITATIONS_PER_SENTENCE = 2;

    while (remaining.length > 0) {
      // Check for sentence boundaries to reset citation counter
      const sentenceEnd = remaining.match(/[.!?]\s/);
      if (sentenceEnd && sentenceEnd.index === 0) {
        citationsInSentence = 0;
      }

      // Citations: (Page X) or [Page X] or similar patterns
      const citationMatch = remaining.match(/\(([^)]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^)]*)\)|\[([^\]]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^\]]*)\]/);
      
      if (citationMatch) {
        const beforeCitation = remaining.slice(0, citationMatch.index);
        const citation = citationMatch[1] || citationMatch[2];
        
        // Add text before citation
        if (beforeCitation) {
          parts.push(...processTextFormatting(beforeCitation, keyCounter++));
        }

        // Get citation info (number and image)
        const citationInfo = getCitationInfo(citation);

        // Only render if we haven't exceeded max citations per sentence and citation exists
        if (citationInfo && citationsInSentence < MAX_CITATIONS_PER_SENTENCE) {
          citationsInSentence++;
          
          // Render numbered superscript with hover card
          parts.push(
            <CitationHoverCard
              key={`cite-${keyCounter++}`}
              number={citationInfo.number}
              imageUrl={citationInfo.image.url!}
              label={citationInfo.image.label || citation}
              score={citationInfo.image.score || undefined}
              onOpen={() => {
                if (citationInfo.image.url) {
                  onImageClick?.(citationInfo.image.url, citationInfo.image.label || undefined);
                }
              }}
            />
          );
        }

        remaining = remaining.slice(citationMatch.index! + citationMatch[0].length);
      } else {
        // No more citations, process remaining text
        parts.push(...processTextFormatting(remaining, keyCounter++));
        break;
      }
    }

    return parts;
  };

  const processTextFormatting = (text: string, baseKey: number): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let keyCounter = 0;

    while (remaining.length > 0) {
      // Bold: **text**
      const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
      if (boldMatch && boldMatch.index !== undefined) {
        if (boldMatch.index > 0) {
          parts.push(remaining.slice(0, boldMatch.index));
        }
        parts.push(
          <strong key={`${baseKey}-bold-${keyCounter++}`} className="font-semibold text-foreground">
            {boldMatch[1]}
          </strong>
        );
        remaining = remaining.slice(boldMatch.index + boldMatch[0].length);
        continue;
      }

      // Italic: *text* (but not **)
      const italicMatch = remaining.match(/(?<!\*)\*([^*]+)\*(?!\*)/);
      if (italicMatch && italicMatch.index !== undefined) {
        if (italicMatch.index > 0) {
          parts.push(remaining.slice(0, italicMatch.index));
        }
        parts.push(
          <em key={`${baseKey}-italic-${keyCounter++}`} className="italic">
            {italicMatch[1]}
          </em>
        );
        remaining = remaining.slice(italicMatch.index + italicMatch[0].length);
        continue;
      }

      // Inline code: `code`
      const codeMatch = remaining.match(/`([^`]+)`/);
      if (codeMatch && codeMatch.index !== undefined) {
        if (codeMatch.index > 0) {
          parts.push(remaining.slice(0, codeMatch.index));
        }
        parts.push(
          <code
            key={`${baseKey}-code-${keyCounter++}`}
            className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono border"
          >
            {codeMatch[1]}
          </code>
        );
        remaining = remaining.slice(codeMatch.index + codeMatch[0].length);
        continue;
      }

      // No more formatting, add remaining text
      parts.push(remaining);
      break;
    }

    return parts;
  };

  return (
    <div className="markdown-content prose prose-sm max-w-none">
      {renderContent()}
    </div>
  );
}
