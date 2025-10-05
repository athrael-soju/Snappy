import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Image as ImageIcon, Layers, Search, GitCompare, Sparkles, Database, Server, Code, Rocket, CloudUpload, Eye, Brain, Shield } from "lucide-react";

export default function AboutContent({ onClose }: { onClose?: () => void }) {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
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
            <Card className="border-2 border-blue-200/50 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 shadow-lg hover:shadow-xl transition-shadow duration-300">
              <CardHeader className="pb-3">
                <CardDescription className="max-w-prose leading-relaxed">
                  A full-stack multimodal RAG system combining FastAPI, Next.js, and ColQwen2.5 for visual document understanding. Optimized for scanned documents, forms, tables, and complex layouts where traditional text-only RAG falls short.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-3 text-sm text-muted-foreground">
                {[{
                  icon: Database, text: "Qdrant with binary quantization, multi-vector search, and optional MUVERA"
                },{
                  icon: Server, text: "MinIO with parallel uploads (12 workers), JPEG quality control, and public URLs"
                },{
                  icon: Layers, text: "FastAPI with pipelined indexing (3-batch concurrency), SSE progress streaming"
                },{
                  icon: Search, text: "Next.js 15 with Edge Runtime chat, localStorage config, and real-time UI"
                },{
                  icon: ImageIcon, text: "ColQwen2.5 multi-vector embeddings with mean pooling for rows/cols"
                },{
                  icon: Sparkles, text: "Runtime configuration UI, health checks, and maintenance endpoints"
                }].map((item, i) => {
                  const I = item.icon;
                  return (
                    <div key={i} className="flex items-start gap-2">
                      <I className="w-4 h-4 text-blue-600 mt-0.5" />
                      <span>{item.text}</span>
                    </div>
                  );
                })}
                </div>
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
            <Card className="border-2 border-cyan-200/50 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 shadow-lg hover:shadow-xl transition-shadow duration-300">
              <CardContent className="pt-4 text-muted-foreground space-y-3 max-w-prose">
                <p className="leading-relaxed">
                  <strong className="text-foreground">ColPali</strong> (Contextualized Late Interaction over PaliGemma) is a state-of-the-art visual document retrieval method that treats entire page images as multi-vector embeddings. This template uses <strong className="text-foreground">ColQwen2.5</strong>, a 7B parameter vision-language model fine-tuned for document understanding.
                </p>
                <p className="leading-relaxed">
                  Instead of extracting text via OCR and losing layout information, ColPali generates <strong className="text-foreground">128 patch embeddings per image</strong> (1024 dimensions each). Your query is compared against all patches using <strong className="text-foreground">MaxSim scoring</strong> - finding the maximum similarity between query tokens and image patches.
                </p>
                <p className="leading-relaxed">
                  The system performs <strong className="text-foreground">mean pooling across rows and columns</strong> to create additional pooled vectors, enabling both fine-grained patch-level matching and holistic document-level retrieval. Binary quantization (32x compression) accelerates search while maintaining accuracy through full-precision rescoring.
                </p>
                <p className="leading-relaxed">
                  This approach preserves visual layout, typography, tables, charts, and handwriting - making it ideal for scanned documents, forms, invoices, and any content where visual structure matters.
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
              <Card className="border-2 border-amber-200/50 bg-gradient-to-br from-amber-500/5 to-orange-500/5 shadow-md hover:shadow-lg transition-shadow duration-300">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Layers className="w-5 h-5 text-amber-600" />
                      <CardTitle className="text-base font-semibold">Traditional RAG</CardTitle>
                    </div>
                    <Badge variant="outline" className="text-xs">Baseline</Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-2">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Text extraction:</strong> OCR or PDF text parsing required</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Performance:</strong> Fast for clean, well-formatted documents</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Limitations:</strong> Loses layout, struggles with tables/charts/handwriting</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Storage:</strong> Compact text chunks (typically 512 tokens)</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Best for:</strong> Blogs, documentation, clean PDFs</span></li>
                  </ul>
                </CardContent>
              </Card>
              <Card className="border-2 border-emerald-200/50 bg-gradient-to-br from-emerald-500/5 to-green-500/5 shadow-md hover:shadow-lg transition-shadow duration-300">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ImageIcon className="w-5 h-5 text-emerald-600" />
                      <CardTitle className="text-base font-semibold">ColPali</CardTitle>
                    </div>
                    <Badge className="text-xs">High recall</Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-2">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Visual understanding:</strong> No OCR - processes images directly</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Performance:</strong> 128 patch embeddings per page with multi-vector search</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Strengths:</strong> Preserves layout, handles tables/charts/handwriting naturally</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Storage:</strong> Larger vectors (128×1024D) but 32x compressed via quantization</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span><strong>Best for:</strong> Scanned docs, forms, receipts, complex layouts</span></li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="tech-stack">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <Code className="w-5 h-5 text-violet-600" />
              <span className="font-semibold">Technical Stack & Features</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-2">
              <Card className="border-2 border-violet-200/50 bg-gradient-to-br from-violet-500/5 to-purple-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Server className="w-5 h-5 text-violet-600" />
                    <CardTitle className="text-sm">Backend</CardTitle>
                  </div>
                  <CardDescription className="text-xs">Python/FastAPI</CardDescription>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-1.5"><span>•</span><span>Modular routers</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>Pipelined indexing (3-batch)</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>SSE progress streaming</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>Runtime config API</span></li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="border-2 border-blue-200/50 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Code className="w-5 h-5 text-blue-600" />
                    <CardTitle className="text-sm">Frontend</CardTitle>
                  </div>
                  <CardDescription className="text-xs">Next.js 15/React</CardDescription>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-1.5"><span>•</span><span>Edge Runtime chat</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>shadcn/ui + Tailwind</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>OpenAPI SDK + Zod</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>Zustand + localStorage</span></li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="border-2 border-emerald-200/50 bg-gradient-to-br from-emerald-500/5 to-green-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Database className="w-5 h-5 text-emerald-600" />
                    <CardTitle className="text-sm">Vector DB</CardTitle>
                  </div>
                  <CardDescription className="text-xs">Qdrant</CardDescription>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-1.5"><span>•</span><span>Binary quantization (32x)</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>Multi-vector search</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>Optional MUVERA</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>On-disk storage</span></li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="border-2 border-amber-200/50 bg-gradient-to-br from-amber-500/5 to-orange-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <Layers className="w-5 h-5 text-amber-600" />
                    <CardTitle className="text-sm">Storage</CardTitle>
                  </div>
                  <CardDescription className="text-xs">MinIO</CardDescription>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">
                  <ul className="space-y-1">
                    <li className="flex items-start gap-1.5"><span>•</span><span>Parallel uploads (12 workers)</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>JPEG/PNG/WebP support</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>Public URL generation</span></li>
                    <li className="flex items-start gap-1.5"><span>•</span><span>Retry logic + fail-fast</span></li>
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
            <Card className="border-2 border-purple-200/50 bg-gradient-to-br from-purple-500/5 to-pink-500/5 shadow-lg hover:shadow-xl transition-shadow duration-300">
              <CardContent className="pt-4 text-muted-foreground space-y-3 max-w-prose">
                <div className="space-y-2">
                  <p className="leading-relaxed"><strong className="text-foreground">Choose Text-only RAG when:</strong></p>
                  <ul className="space-y-1 ml-4">
                    <li className="flex items-start gap-2"><span>•</span><span>Documents are clean, digital-native (blogs, code, markdown)</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>Storage and compute constraints are tight</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>Visual layout and formatting don't matter</span></li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <p className="leading-relaxed"><strong className="text-foreground">Choose ColPali when:</strong></p>
                  <ul className="space-y-1 ml-4">
                    <li className="flex items-start gap-2"><span>•</span><span>Documents are scanned, contain complex tables, charts, or handwriting</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>Visual layout carries semantic meaning (forms, invoices, receipts)</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>OCR quality is poor or unreliable</span></li>
                    <li className="flex items-start gap-2"><span>•</span><span>You need high recall on visual/spatial cues</span></li>
                  </ul>
                </div>
                <p className="pt-2 border-t leading-relaxed"><strong className="text-foreground">Hybrid approach:</strong> This template can be extended to combine both methods - use ColPali for visual-heavy pages and text embeddings for clean documents.</p>
              </CardContent>
            </Card>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="getting-started">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <Rocket className="w-5 h-5 text-cyan-600" />
              <span className="font-semibold">Where do I start?</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4">
              <p className="text-muted-foreground text-center leading-relaxed">
                Get started with this template in four simple steps:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-2">
                {/* Step 1: Upload */}
                <Card className="border-2 border-blue-200/50 bg-gradient-to-br from-blue-500/5 to-purple-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white flex items-center justify-center font-bold text-sm">1</div>
                      <CloudUpload className="w-5 h-5 text-blue-600" />
                    </div>
                    <CardTitle className="text-base font-semibold">Upload Documents</CardTitle>
                    <CardDescription className="text-xs">
                      Upload PDFs, forms, or scanned documents for automatic processing
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button asChild className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-md hover:shadow-lg transition-all duration-300 rounded-full h-9 text-sm">
                      <Link href="/upload" onClick={() => onClose?.()}>
                        Go to Upload
                      </Link>
                    </Button>
                  </CardContent>
                </Card>

                {/* Step 2: Search */}
                <Card className="border-2 border-cyan-200/50 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 text-white flex items-center justify-center font-bold text-sm">2</div>
                      <Eye className="w-5 h-5 text-cyan-600" />
                    </div>
                    <CardTitle className="text-base font-semibold">Search Documents</CardTitle>
                    <CardDescription className="text-xs">
                      Use natural language to find pages with visual understanding
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button asChild variant="outline" className="w-full border-2 border-cyan-200/50 hover:border-cyan-400 hover:bg-gradient-to-r hover:from-cyan-50 hover:to-blue-50 rounded-full h-9 text-sm">
                      <Link href="/search" onClick={() => onClose?.()}>
                        Try Search
                      </Link>
                    </Button>
                  </CardContent>
                </Card>

                {/* Step 3: Chat */}
                <Card className="border-2 border-purple-200/50 bg-gradient-to-br from-purple-500/5 to-pink-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white flex items-center justify-center font-bold text-sm">3</div>
                      <Brain className="w-5 h-5 text-purple-600" />
                    </div>
                    <CardTitle className="text-base font-semibold">Chat with AI</CardTitle>
                    <CardDescription className="text-xs">
                      Ask questions with answers backed by visual citations
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button asChild variant="outline" className="w-full border-2 border-purple-200/50 hover:border-purple-400 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 rounded-full h-9 text-sm">
                      <Link href="/chat" onClick={() => onClose?.()}>
                        Start Chatting
                      </Link>
                    </Button>
                  </CardContent>
                </Card>

                {/* Step 4: Maintenance */}
                <Card className="border-2 border-red-200/50 bg-gradient-to-br from-red-500/5 to-orange-500/5 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500 to-orange-500 text-white flex items-center justify-center font-bold text-sm">4</div>
                      <Shield className="w-5 h-5 text-red-600" />
                    </div>
                    <CardTitle className="text-base font-semibold">Maintenance</CardTitle>
                    <CardDescription className="text-xs">
                      Manage data, configure settings, and monitor system health
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button asChild variant="outline" className="w-full border-2 border-red-200/50 hover:border-red-400 hover:bg-gradient-to-r hover:from-red-50 hover:to-orange-50 rounded-full h-9 text-sm">
                      <Link href="/maintenance" onClick={() => onClose?.()}>
                        Maintenance
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              </div>
              
              <div className="pt-2 border-t">
                <Button asChild variant="ghost" className="text-muted-foreground hover:text-blue-600 rounded-full w-full">
                  <Link href="https://github.com/athrael-soju/fastapi-nextjs-colpali-template" target="_blank" rel="noreferrer">
                    View Documentation on GitHub →
                  </Link>
                </Button>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
