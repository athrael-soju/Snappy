import Link from "next/link"
import { Heart } from "lucide-react"

export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="relative border-t border-border/40 bg-background/80 backdrop-blur-xl">
      {/* Subtle gradient line at bottom */}
      <div className="absolute inset-x-0 bottom-0 h-[1px] bg-gradient-to-r from-transparent via-primary/20 to-transparent" />
      
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p className="text-center text-base text-muted-foreground sm:text-left">
            © {currentYear} <span className="font-semibold text-foreground">Snappy!</span> Crafted for lightning-fast visual retrieval.
          </p>
          
          <div className="flex flex-wrap items-center justify-center gap-2 text-base text-muted-foreground">
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
            <Heart className="ml-2 h-5 w-5 fill-primary text-primary transition-transform hover:scale-110" aria-hidden />
          </div>
        </div>
      </div>
    </footer>
  )
}
