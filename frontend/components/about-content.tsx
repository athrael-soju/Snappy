import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
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
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-700 to-cyan-700 bg-clip-text text-transparent">About this Template</h1>
            <p className="text-muted-foreground text-lg">What this template does, what ColPali is, and how it differs from traditional RAG</p>
          </div>
        </div>
      </div>

      {/* Progressive disclosure via Accordion */}
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="overview">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              <span className="font-semibold">Project Overview</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <Card className="border-blue-200/60">
              <CardHeader className="pb-2">
                <CardDescription>
                  Upload, index, and search/chat over your documents and images. Visual-first retrieval with ColPali.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid sm:grid-cols-2 gap-3 text-sm text-muted-foreground">
                {[{
                  icon: Database, text: "Qdrant stores vectors (searchable representations)."
                },{
                  icon: Server, text: "MinIO stores original files and previews."
                },{
                  icon: Layers, text: "FastAPI provides indexing and maintenance APIs."
                },{
                  icon: Search, text: "Next.js provides upload, search, chat, and admin UI."
                },{
                  icon: ImageIcon, text: "ColPali creates image-based representations for strong recall."
                },{
                  icon: Sparkles, text: "Great for scans, forms, tables, and visual layouts."
                }].map((item, i) => {
                  const I = item.icon;
                  return (
                    <div key={i} className="flex items-start gap-2">
                      <I className="w-4 h-4 text-blue-600 mt-0.5" />
                      <span>{item.text}</span>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="colpali">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <ImageIcon className="w-5 h-5 text-cyan-600" />
              <span className="font-semibold">What is ColPali?</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <Card className="border-cyan-200/60">
              <CardContent className="pt-4 text-sm text-muted-foreground space-y-3">
                <p>
                  ColPali is a visual search method. It compares your question to many small features in a page image to find matches.
                </p>
                <p className="flex items-center gap-2">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="underline underline-offset-2 cursor-help">Embeddings</span>
                    </TooltipTrigger>
                    <TooltipContent>Numeric vectors that represent content for similarity search.</TooltipContent>
                  </Tooltip>
                  help the system measure similarity.
                </p>
                <p>
                  This keeps layout and visuals intact and reduces reliance on OCR.
                </p>
              </CardContent>
            </Card>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="compare">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-emerald-600" />
              <span className="font-semibold">ColPali vs. Text-only RAG</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card className="border-amber-200/60">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Layers className="w-5 h-5 text-amber-600" />
                      <CardTitle className="text-base">Traditional RAG</CardTitle>
                    </div>
                    <Badge variant="outline" className="text-xs">Baseline</Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-2">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-2"><span>•</span><span>Fast for clean text.</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>Needs good OCR for scans.</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>May miss tables/figures.</span></li>
                  </ul>
                </CardContent>
              </Card>
              <Card className="border-emerald-200/60">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ImageIcon className="w-5 h-5 text-emerald-600" />
                      <CardTitle className="text-base">ColPali</CardTitle>
                    </div>
                    <Badge className="text-xs">High recall</Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-2">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-2"><span>•</span><span>Great on scans and complex layouts.</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>Finds small visual/text cues.</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>Less dependent on OCR.</span></li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="guidance">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <span className="font-semibold">When should I use it?</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <Card className="border-purple-200/60">
              <CardContent className="pt-4 text-sm text-muted-foreground space-y-2">
                <ul className="space-y-1">
                  <li className="flex items-start gap-2"><span>•</span><span><strong>Text-only RAG</strong> for blogs, docs, code.</span></li>
                  <li className="flex items-start gap-2"><span>•</span><span><strong>ColPali</strong> for scanned PDFs, forms, receipts, tables.</span></li>
                  <li className="flex items-start gap-2"><span>•</span><span>Hybrid can combine both.</span></li>
                </ul>
              </CardContent>
            </Card>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Next-step CTAs */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
        <Button asChild className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
          <Link href="/upload">Start by uploading a file</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/search">Try a search</Link>
        </Button>
        <Button asChild variant="ghost" className="text-muted-foreground">
          <Link href="https://github.com/athrael-soju/fastapi-nextjs-colpali-template" target="_blank" rel="noreferrer">Learn more</Link>
        </Button>
      </div>
    </div>
  );
}
