import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import CitationHoverCard from "@/components/chat/CitationHoverCard";
import type { ChatCitation } from "./chat-message";

type MarkdownRendererProps = {
    content: string;
    citations?: ChatCitation[];
    onCitationOpen?: (url: string, label?: string | null) => void;
};

export default function MarkdownRenderer({
    content,
    citations,
    onCitationOpen
}: MarkdownRendererProps) {
    // Build citation map
    const citationMap = useMemo(() => {
        const map = new Map<string, { number: number; citation: ChatCitation }>();

        citations?.forEach((citation, index) => {
            if (citation.url) {
                const info = { number: index + 1, citation };
                map.set(citation.url, info);
            }
        });

        return map;
    }, [citations]);

    // Custom component to render grouped citations
    const renderGroupedCitations = (children: any) => {
        // Check if we're in a Sources section with multiple list items
        const listItems: any[] = [];
        const processChild = (child: any) => {
            if (child?.type === 'li' || child?.props?.node?.tagName === 'li') {
                listItems.push(child);
            }
        };

        if (Array.isArray(children)) {
            children.forEach(processChild);
        } else {
            processChild(children);
        }

        // If we have list items, try to group them
        if (listItems.length > 0) {
            const renderedGroups = new Map<string, any>();

            listItems.forEach((item: any) => {
                // Find the link in this list item
                const findLink = (node: any): { href?: string; label?: string } => {
                    if (node?.props?.href) {
                        return { href: node.props.href, label: node.props.children };
                    }
                    if (node?.props?.children) {
                        const children = Array.isArray(node.props.children) ? node.props.children : [node.props.children];
                        for (const child of children) {
                            const result = findLink(child);
                            if (result.href) return result;
                        }
                    }
                    return {};
                };

                const { href } = findLink(item);
                if (!href) return;

                const citationInfo = citationMap.get(href);
                if (!citationInfo) return;

                const label = citationInfo.citation.label || '';
                const filenameMatch = label.match(/^(.+?)\s*-\s*(?:Page|page|p\.)\s*(\d+)/);
                const filename = filenameMatch ? filenameMatch[1].trim() : label;

                if (!renderedGroups.has(filename)) {
                    renderedGroups.set(filename, []);
                }
                renderedGroups.get(filename)!.push({ href, citationInfo, label });
            });

            // Render grouped citations
            const result: any[] = [];
            let groupIndex = 0;

            renderedGroups.forEach((group, filename) => {
                if (group.length === 1) {
                    // Single citation - render normally
                    const { href, citationInfo, label } = group[0];
                    result.push(
                        <li key={`citation-${groupIndex++}`} className="ml-4">
                            <CitationHoverCard
                                number={citationInfo.number}
                                imageUrl={href}
                                label={citationInfo.citation.label || label}
                                score={citationInfo.citation.score}
                                onOpen={() => onCitationOpen?.(href, citationInfo.citation.label)}
                            >
                                <a
                                    href="#"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        onCitationOpen?.(href, citationInfo.citation.label);
                                    }}
                                    className="text-primary hover:underline cursor-pointer"
                                >
                                    {label}
                                </a>
                            </CitationHoverCard>
                        </li>
                    );
                } else {
                    // Multiple citations from same file - group them
                    result.push(
                        <li key={`citation-group-${groupIndex++}`} className="ml-4">
                            <span className="font-medium">{filename}</span>
                            <span className="ml-2">
                                {group.map((item: any, idx: number) => {
                                    const { href, citationInfo, label } = item;
                                    const pageMatch = label.match(/(?:Page|page|p\.)\s*(\d+)/);
                                    const pageText = pageMatch ? `Page ${pageMatch[1]}` : label;

                                    return (
                                        <span key={`page-${idx}`}>
                                            {idx > 0 && ', '}
                                            <CitationHoverCard
                                                number={citationInfo.number}
                                                imageUrl={href}
                                                label={citationInfo.citation.label || label}
                                                score={citationInfo.citation.score}
                                                onOpen={() => onCitationOpen?.(href, citationInfo.citation.label)}
                                            >
                                                <a
                                                    href="#"
                                                    onClick={(e) => {
                                                        e.preventDefault();
                                                        onCitationOpen?.(href, citationInfo.citation.label);
                                                    }}
                                                    className="text-primary hover:underline cursor-pointer"
                                                >
                                                    {pageText}
                                                </a>
                                            </CitationHoverCard>
                                        </span>
                                    );
                                })}
                            </span>
                        </li>
                    );
                }
            });

            return result;
        }

        return children;
    };

    return (
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
                // Style paragraphs
                p: ({ children, ...props }) => (
                    <p className="mb-2 last:mb-0" {...props}>
                        {children}
                    </p>
                ),
                // Style code blocks
                code: ({ inline, className, children, ...props }: any) => {
                    return inline ? (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                            {children}
                        </code>
                    ) : (
                        <code className="block bg-muted p-3 rounded-lg text-sm font-mono overflow-x-auto my-2" {...props}>
                            {children}
                        </code>
                    );
                },
                // Style list items
                li: ({ children, ...props }) => (
                    <li className="ml-4" {...props}>
                        {children}
                    </li>
                ),
                // Handle citation links
                a: ({ href, children, ...props }) => {
                    // Check if this is a citation link
                    const citationInfo = href ? citationMap.get(href) : undefined;

                    if (citationInfo && href) {
                        // Render citation as a clickable link with hover card
                        const label = typeof children === 'string' ? children :
                                     Array.isArray(children) ? children.join('') : 'Unknown';

                        return (
                            <CitationHoverCard
                                number={citationInfo.number}
                                imageUrl={href}
                                label={citationInfo.citation.label || label}
                                score={citationInfo.citation.score}
                                onOpen={() => onCitationOpen?.(href, citationInfo.citation.label)}
                            >
                                <a
                                    href="#"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        onCitationOpen?.(href, citationInfo.citation.label);
                                    }}
                                    className="text-primary hover:underline cursor-pointer"
                                >
                                    {label}
                                </a>
                            </CitationHoverCard>
                        );
                    }

                    // Regular link
                    return (
                        <a
                            href={href}
                            className="text-primary hover:underline"
                            target="_blank"
                            rel="noopener noreferrer"
                            {...props}
                        >
                            {children}
                        </a>
                    );
                },
                // Style lists
                ul: ({ children, ...props }) => (
                    <ul className="list-disc list-inside space-y-1 my-2" {...props}>
                        {children}
                    </ul>
                ),
                ol: ({ children, ...props }) => (
                    <ol className="list-decimal list-inside space-y-1 my-2" {...props}>
                        {renderGroupedCitations(children)}
                    </ol>
                ),
                // Style headings
                h1: ({ children, ...props }) => (
                    <h1 className="text-2xl font-bold mt-4 mb-2" {...props}>
                        {children}
                    </h1>
                ),
                h2: ({ children, ...props }) => (
                    <h2 className="text-xl font-bold mt-3 mb-2" {...props}>
                        {children}
                    </h2>
                ),
                h3: ({ children, ...props }) => (
                    <h3 className="text-lg font-semibold mt-2 mb-1" {...props}>
                        {children}
                    </h3>
                ),
                // Style horizontal rules
                hr: ({ ...props }) => (
                    <hr className="my-4 border-border" {...props} />
                ),
                // Style blockquotes
                blockquote: ({ children, ...props }) => (
                    <blockquote className="border-l-4 border-primary/50 pl-4 italic my-2" {...props}>
                        {children}
                    </blockquote>
                ),
                // Style tables (GFM)
                table: ({ children, ...props }) => (
                    <div className="overflow-x-auto my-4">
                        <table className="min-w-full border-collapse border border-border" {...props}>
                            {children}
                        </table>
                    </div>
                ),
                th: ({ children, ...props }) => (
                    <th className="border border-border px-4 py-2 bg-muted font-semibold text-left" {...props}>
                        {children}
                    </th>
                ),
                td: ({ children, ...props }) => (
                    <td className="border border-border px-4 py-2" {...props}>
                        {children}
                    </td>
                ),
                // Style strikethrough (GFM)
                del: ({ children, ...props }) => (
                    <del className="line-through opacity-75" {...props}>
                        {children}
                    </del>
                ),
                // Style strong/bold
                strong: ({ children, ...props }) => (
                    <strong className="font-semibold" {...props}>
                        {children}
                    </strong>
                ),
                // Style emphasis/italic
                em: ({ children, ...props }) => (
                    <em className="italic" {...props}>
                        {children}
                    </em>
                ),
            }}
        >
            {content}
        </ReactMarkdown>
    );
}
