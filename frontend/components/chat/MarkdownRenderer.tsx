"use client";

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { FileText, ExternalLink } from 'lucide-react';
import Image from 'next/image';

interface ImageData {
  url: string | null;
  label: string | null;
  score: number | null;
}

interface MarkdownRendererProps {
  content: string;
  images?: ImageData[];
  onCitationClick?: (citation: string) => void;
  onImageClick?: (url: string, label?: string) => void;
}

/**
 * Renders markdown-formatted text with special handling for citations.
 * Supports:
 * - **bold** text
 * - *italic* text
 * - `code` inline
 * - ```code blocks```
 * - # Headers
 * - - Lists
 * - [Page X](citation) or (Page X) citations with visual badges
 */
export default function MarkdownRenderer({ content, images = [], onCitationClick, onImageClick }: MarkdownRendererProps) {
  // Helper to find matching image by label
  const findImageByLabel = (citation: string): ImageData | undefined => {
    if (!images || images.length === 0) return undefined;
    
    // Try to match the citation text with image labels
    return images.find(img => 
      img.label && citation.toLowerCase().includes(img.label.toLowerCase())
    );
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
            <pre key={`code-${lineIdx}`} className="bg-muted/50 rounded-lg p-4 my-3 overflow-x-auto border">
              <code className="text-sm font-mono text-foreground">
                {codeBlockContent.join('\n')}
              </code>
            </pre>
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

    while (remaining.length > 0) {
      // Citations: (Page X) or [Page X] or similar patterns
      const citationMatch = remaining.match(/\(([^)]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^)]*)\)|\[([^\]]*(?:page|Page|PAGE|p\.|P\.)\s*\d+[^\]]*)\]/);
      
      if (citationMatch) {
        const beforeCitation = remaining.slice(0, citationMatch.index);
        const citation = citationMatch[1] || citationMatch[2];
        
        // Add text before citation
        if (beforeCitation) {
          parts.push(...processTextFormatting(beforeCitation, keyCounter++));
        }

        // Try to find matching image
        const matchedImage = findImageByLabel(citation);

        if (matchedImage && matchedImage.url) {
          // Render inline image thumbnail
          parts.push(
            <span
              key={`cite-img-${keyCounter++}`}
              className="inline-flex items-center gap-1.5 mx-1 px-2 py-1 bg-purple-50 border border-purple-200 rounded-lg cursor-pointer hover:bg-purple-100 hover:border-purple-300 transition-all group"
              onClick={() => {
                onImageClick?.(matchedImage.url!, matchedImage.label || undefined);
                onCitationClick?.(citation);
              }}
            >
              <div className="relative w-12 h-12 rounded overflow-hidden border border-purple-200 flex-shrink-0">
                <img
                  src={matchedImage.url}
                  alt={matchedImage.label || 'Citation'}
                  className="w-full h-full object-cover group-hover:scale-110 transition-transform"
                />
              </div>
              <div className="flex flex-col items-start">
                <span className="text-xs font-medium text-purple-800 leading-tight">
                  {matchedImage.label || citation}
                </span>
                {matchedImage.score && (
                  <span className="text-[10px] text-purple-600">
                    {(matchedImage.score * 100).toFixed(0)}% match
                  </span>
                )}
              </div>
              <ExternalLink className="w-3 h-3 text-purple-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            </span>
          );
        } else {
          // Fallback to badge if no image found
          parts.push(
            <Badge
              key={`cite-${keyCounter++}`}
              variant="secondary"
              className="mx-1 cursor-pointer hover:bg-purple-200 transition-colors bg-purple-100 text-purple-800 border border-purple-300"
              onClick={() => onCitationClick?.(citation)}
            >
              <FileText className="w-3 h-3 mr-1" />
              {citation}
            </Badge>
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
