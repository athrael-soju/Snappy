import Link from "next/link"
import { Heart } from "lucide-react"

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="relative shrink-0 border-t border-border/40 bg-background/50 backdrop-blur-xl">
      {/* Subtle gradient line at bottom */}
      <div className="absolute inset-x-0 bottom-0 h-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
      
      <div className="container mx-auto px-4 py-2 sm:py-3">
        <div className="flex flex-col items-center justify-between gap-2 sm:flex-row sm:gap-4">
          <p className="text-center text-xs text-muted-foreground sm:text-left sm:text-sm">
            © {currentYear} <span className="font-semibold text-foreground">Snappy!</span> Crafted for lightning-fast visual retrieval.
          </p>
          
          <div className="flex flex-wrap items-center justify-center gap-x-1.5 gap-y-1 text-xs text-muted-foreground sm:gap-x-2 sm:text-sm">
            <span>Powered by</span>
            <Link 
              href="https://fastapi.tiangolo.com" 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-semibold text-primary transition-colors hover:text-primary/80 hover:underline"
            >
              FastAPI
            </Link>
            <span>,</span>
            <Link 
              href="https://nextjs.org" 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-semibold text-primary transition-colors hover:text-primary/80 hover:underline"
            >
              Next.js
            </Link>
            <span>, and the</span>
            <Link 
              href="https://github.com/illuin-tech/colpali" 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-semibold text-primary transition-colors hover:text-primary/80 hover:underline"
            >
              ColPali
            </Link>
            <span>vision stack</span>
            <Heart className="ml-1 h-4 w-4 fill-primary text-primary transition-transform hover:scale-110 sm:ml-2 sm:h-5 sm:w-5" aria-hidden />
          </div>
        </div>
      </div>
    </footer>
  )
}
