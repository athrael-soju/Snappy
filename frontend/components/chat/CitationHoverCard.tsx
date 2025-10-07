"use client";

import React from 'react';
import Image from "next/image";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { ExternalLink } from 'lucide-react';

interface CitationHoverCardProps {
  number: number;
  imageUrl: string;
  label: string;
  score?: number;
  onOpen: () => void;
  children?: React.ReactNode;
}

/**
 * Hover card that shows citation preview on superscript hover
 */
export default function CitationHoverCard({
  number,
  imageUrl,
  label,
  score,
  onOpen,
  children
}: CitationHoverCardProps) {
  // Extract document title and page info heuristically
  const delimiterIndex = label.toLowerCase().indexOf("page ");
  const docTitle = delimiterIndex >= 0
    ? label.slice(0, delimiterIndex).trim().replace(/["']+$/, "")
    : label;
  const pageInfo = delimiterIndex >= 0 ? label.slice(delimiterIndex).trim() : label;

  return (
    <HoverCard openDelay={200} closeDelay={100}>
      <HoverCardTrigger asChild>
        {children || (
          <sup
            className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-semibold text-purple-700 bg-purple-100 border border-purple-300 rounded cursor-pointer hover:bg-purple-200 hover:border-purple-400 transition-all ml-0.5"
          >
            {number}
          </sup>
        )}
      </HoverCardTrigger>
      <HoverCardContent 
        className="w-80 p-0 overflow-hidden" 
        side="top"
        align="center"
      >
        <div className="flex flex-col">
          {/* Preview Image */}
          <div className="relative w-full h-[120px] bg-gray-100 overflow-hidden border-b">
            <Image
              src={imageUrl}
              alt={label}
              fill
              sizes="320px"
              className="object-contain"
              unoptimized
            />
          </div>
          
          {/* Content */}
          <div className="p-3 space-y-2">
            {/* Document title */}
            <div className="text-xs font-medium text-gray-900 line-clamp-1" title={docTitle}>
              {docTitle}
            </div>
            
            {/* Page info */}
            <div className="text-xs text-gray-600">
              {pageInfo}
            </div>
            
            {/* Score if available */}
            {score !== undefined && score !== null && (
              <div className="text-xs text-purple-600 font-medium">
                {score.toFixed(2)}% relevance
              </div>
            )}
            
            {/* Open button */}
            <button
              onClick={(e) => {
                e.preventDefault();
                onOpen();
              }}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 mt-2 text-xs font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-md transition-colors"
            >
              <span>View Citation</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}
