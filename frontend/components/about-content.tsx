import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Info, Image as ImageIcon, Layers, Search, GitCompare, Sparkles, Database, Server } from "lucide-react";

export default function AboutContent() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-lg border border-blue-500/20">
            <Info className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-700 to-cyan-700 bg-clip-text text-transparent">About this Project</h1>
            <p className="text-muted-foreground text-lg">What this template does, what ColPali is, and how it differs from traditional RAG</p>
          </div>
        </div>
      </div>

      {/* Project Overview */}
      <Card className="border-blue-200/60">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <CardTitle>Project Overview</CardTitle>
          </div>
          <CardDescription>
            A full-stack template that lets you <strong>upload</strong> documents/images, <strong>index</strong> them, and <strong>search/chat</strong> over them using a visual-first retriever (ColPali).
          </CardDescription>
        </CardHeader>
        <CardContent className="grid sm:grid-cols-2 gap-4 text-sm text-muted-foreground">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-600" />
              <span>Qdrant as the vector database for storing dense representations</span>
            </div>
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-600" />
              <span>MinIO object storage for original uploads and thumbnails</span>
            </div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-blue-600" />
              <span>FastAPI backend for indexing/maintenance APIs</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-blue-600" />
              <span>Next.js frontend for search, chat, upload, and admin flows</span>
            </div>
            <div className="flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-blue-600" />
              <span>ColPali encodes pages/images for high-recall retrieval without OCR</span>
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Designed for visually rich documents (scans, forms, tables)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* What is ColPali */}
      <Card className="border-cyan-200/60">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-cyan-600" />
            <CardTitle>What is ColPali?</CardTitle>
          </div>
          <CardDescription>
            ColPali is a <strong>visual retrieval</strong> approach that represents each page/image with many fine-grained embeddings and compares them to the query with <em>late interaction</em>. This helps match small visual/textual cues across complex pages.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            Instead of relying only on text chunks, ColPali works directly with rendered pages/images. It preserves layout and visual signals (tables, stamps, signatures, figures) and reduces dependence on OCR quality.
          </p>
          <p>
            In this template, ColPali embeddings are stored in Qdrant. Search ranks pages by query similarity and surfaces the most relevant pages for chat or inspection.
          </p>
        </CardContent>
      </Card>

      {/* Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-amber-200/60">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-amber-600" />
                <CardTitle>Traditional RAG (text-only)</CardTitle>
              </div>
              <Badge variant="outline" className="text-xs">Baseline</Badge>
            </div>
            <CardDescription>Chunk text, embed with a text encoder, vector search, then prompt the LLM with retrieved text.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <ul className="list-disc pl-5 space-y-1">
              <li>Fast and lightweight for clean text corpora</li>
              <li>Requires robust OCR for scanned PDFs; layout often lost</li>
              <li>Chunking can split tables/figures and miss small cues</li>
              <li>Great for web articles, docs, code; weaker on noisy scans</li>
            </ul>
          </CardContent>
        </Card>
        <Card className="border-emerald-200/60">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-emerald-600" />
                <CardTitle>ColPali (visual-first)</CardTitle>
              </div>
              <Badge className="text-xs">High Recall</Badge>
            </div>
            <CardDescription>Encodes pages as images with many local features and compares them to the query via late interaction.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <ul className="list-disc pl-5 space-y-1">
              <li>Works well on scanned documents and complex layouts</li>
              <li>Finds small visual/textual signals (stamps, numbers, table cells)</li>
              <li>Less dependent on OCR; preserves layout context</li>
              <li>Heavier embeddings and compute vs. simple text-only pipelines</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Guidance */}
      <Card className="border-purple-200/60">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            <CardTitle>When to use which?</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <ul className="list-disc pl-5 space-y-1">
            <li>
              <strong>Traditional RAG</strong> for plain text knowledge bases, docs, blogs, code — prioritize speed and simplicity.
            </li>
            <li>
              <strong>ColPali</strong> for scanned PDFs, forms, contracts, tables, receipts, and mixed media where layout and visuals matter.
            </li>
            <li>
              Hybrid setups can combine both for best coverage.
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
