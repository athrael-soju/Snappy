"use client"

import { motion } from "framer-motion"
import { Loader2 } from "lucide-react"

export default function Loading() {
  return (
    <div className="flex h-full w-full items-center justify-center" role="status" aria-live="polite" aria-busy="true">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="relative flex flex-col items-center gap-6"
      >
        {/* Animated gradient spinner */}
        <div className="relative h-24 w-24">
          {/* Pulsing gradient glow - behind everything */}
          <motion.div
            className="absolute -inset-6 rounded-full bg-gradient-to-br from-chart-1/30 via-chart-2/30 to-chart-4/30 blur-2xl"
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.4, 0.7, 0.4],
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
          
          {/* Outer rotating gradient ring */}
          <motion.div
            className="absolute inset-0 rounded-full bg-gradient-to-tr from-chart-1 via-chart-2 to-chart-4 opacity-30 blur-sm"
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear", repeatType: "loop" }}
          />
          
          {/* Main rotating gradient ring */}
          <motion.div
            className="absolute inset-1 rounded-full overflow-hidden"
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "linear", repeatType: "loop" }}
          >
            <div 
              className="h-full w-full"
              style={{
                background: "conic-gradient(from 0deg, transparent 0%, hsl(var(--chart-1)) 25%, hsl(var(--chart-2)) 50%, hsl(var(--chart-4)) 75%, transparent 100%)",
              }}
            />
          </motion.div>
          
          {/* Inner circle - background */}
          <div className="absolute inset-[4px] rounded-full bg-background" />
          
          {/* Center icon - animated */}
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear", repeatType: "loop" }}
            >
              <Loader2 className="size-icon-2xl text-primary" />
            </motion.div>
          </div>
        </div>
        
        {/* Loading text with gradient */}
        <motion.p
          className="bg-gradient-to-r from-chart-1 via-chart-2 to-chart-4 bg-clip-text text-body font-semibold text-transparent"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", repeatType: "loop" }}
        >
          Snappy is getting things ready...
        </motion.p>
      </motion.div>
    </div>
  );
}

