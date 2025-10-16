import Link from "next/link"
import { Heart } from "lucide-react"

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-5 text-base sm:flex-row sm:px-6 lg:px-8">
        <p className="text-center text-muted-foreground sm:text-left">
          © {currentYear} Snappy! Crafted for lightning-fast visual retrieval.
        </p>
        
        <div className="flex flex-wrap items-center justify-center gap-1.5 text-muted-foreground">
          <span>Powered by</span>
          <Link 
            href="https://github.com/illuin-tech/colpali" 
            target="_blank" 
            rel="noopener noreferrer"
            className="font-medium text-primary hover:underline"
          >
            FastAPI
          </Link>
          <span>,</span>
          <Link 
            href="https://nextjs.org" 
            target="_blank" 
            rel="noopener noreferrer"
            className="font-medium text-primary hover:underline"
          >
            Next.js
          </Link>
          <span>, and the</span>
          <Link 
            href="https://github.com/illuin-tech/colpali" 
            target="_blank" 
            rel="noopener noreferrer"
            className="font-medium text-primary hover:underline"
          >
            ColPali
          </Link>
          <span>vision stack</span>
          <Heart className="ml-1.5 h-4 w-4 fill-primary text-primary" aria-hidden />
        </div>
      </div>
    </footer>
  )
}
