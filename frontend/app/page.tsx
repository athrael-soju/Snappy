import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="space-y-12">
      <section className="text-center py-10 sm:py-14">
        <h1 className="text-3xl sm:text-5xl font-bold tracking-tight">
          Search, Upload & Chat with your visual data
        </h1>
        <p className="mt-3 text-sm sm:text-base text-black/70 dark:text-white/70 max-w-2xl mx-auto">
          A modern UI for ColPali-powered visual retrieval augmented generation. Built with Next.js 15 and Tailwind v4.
        </p>
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link href="/search">
            <Button size="lg">Start Searching</Button>
          </Link>
          <Link href="/upload">
            <Button variant="outline" size="lg">Upload Documents</Button>
          </Link>
          <Link href="/chat">
            <Button variant="ghost" size="lg">Open Chat</Button>
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Fast Visual Search</CardTitle>
            <CardDescription>Retrieve relevant images and pages instantly.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">Powered by Qdrant and ColPali embeddings.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Simple Uploads</CardTitle>
            <CardDescription>Batch upload files via MinIO storage.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">Drag-and-drop support coming soon.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Chat Grounded by Images</CardTitle>
            <CardDescription>Ask questions and see supporting visuals.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">Image citations with labels and scores.</p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
