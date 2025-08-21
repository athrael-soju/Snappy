"use client";

import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Settings, Database, Server, Trash2, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

type ActionType = "q" | "m" | "all";

const actions = [
  {
    id: "q" as ActionType,
    title: "Clear Vector Database",
    description: "Remove all document embeddings from Qdrant",
    icon: Database,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    confirmMsg: "This will clear the Qdrant collection. Continue?",
    successMsg: "Qdrant cleared"
  },
  {
    id: "m" as ActionType,
    title: "Clear Object Storage",
    description: "Remove all images from MinIO bucket",
    icon: Server,
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    confirmMsg: "This will clear all images from MinIO. Continue?",
    successMsg: "MinIO cleared"
  },
  {
    id: "all" as ActionType,
    title: "Clear Everything",
    description: "Remove all data from both Qdrant and MinIO",
    icon: Trash2,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    confirmMsg: "This will clear both Qdrant and MinIO. Continue?",
    successMsg: "All data cleared"
  }
];

export default function MaintenancePage() {
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<{ q: boolean; m: boolean; all: boolean }>({ q: false, m: false, all: false });

  async function run(action: ActionType) {
    const actionConfig = actions.find(a => a.id === action);
    if (!actionConfig) return;
    
    if (!confirm(actionConfig.confirmMsg)) return;

    setError(null);
    setStatus("");
    setLoading((s) => ({ ...s, [action]: true }));
    
    try {
      let res: any;
      if (action === "q") res = await MaintenanceService.clearQdrantClearQdrantPost();
      else if (action === "m") res = await MaintenanceService.clearMinioClearMinioPost();
      else res = await MaintenanceService.clearAllClearAllPost();

      const msg = typeof res === "object" && res !== null
        ? (res.message ?? JSON.stringify(res))
        : String(res ?? "Operation completed successfully");
      
      setStatus(msg);
      toast.success(actionConfig.successMsg, { description: msg });
    } catch (err: unknown) {
      let errorMsg = "Maintenance action failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error("Action failed", { description: errorMsg });
    } finally {
      setLoading((s) => ({ ...s, [action]: false }));
    }
  }

  const isAnyLoading = loading.q || loading.m || loading.all;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-500/10 rounded-lg">
            <Settings className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">System Maintenance</h1>
            <p className="text-muted-foreground">Manage your vector database and object storage</p>
          </div>
        </div>
      </div>

      {/* Warning Banner */}
      <Card className="border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30">
        <CardContent className="flex items-center gap-3 p-4">
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0" />
          <div className="space-y-1">
            <div className="font-medium text-amber-800 dark:text-amber-200">
              Destructive Operations
            </div>
            <div className="text-sm text-amber-700 dark:text-amber-300">
              These actions permanently delete data and cannot be undone. Please proceed with caution.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {actions.map((action, index) => {
          const Icon = action.icon;
          const isLoading = loading[action.id];
          
          return (
            <motion.div
              key={action.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="h-full group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <CardHeader className="pb-4">
                  <div className={`inline-flex w-12 h-12 items-center justify-center rounded-xl ${action.color} bg-accent/10 mb-4 group-hover:scale-110 transition-transform`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <CardTitle className="text-xl group-hover:text-foreground/90 transition-colors">
                    {action.title}
                  </CardTitle>
                  <CardDescription className="text-base">
                    {action.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button
                    variant="destructive"
                    onClick={() => run(action.id)}
                    disabled={isAnyLoading}
                    className="w-full"
                    size="lg"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Icon className="w-4 h-4 mr-2" />
                        {action.title}
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Status Messages */}
      <AnimatePresence>
        {status && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex items-center gap-2 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg text-green-800 dark:text-green-200"
            role="status"
          >
            <CheckCircle className="w-5 h-5" />
            <div>
              <div className="font-medium">Operation Completed</div>
              <div className="text-sm opacity-90">{status}</div>
            </div>
          </motion.div>
        )}
        
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200"
            role="alert"
          >
            <AlertTriangle className="w-5 h-5" />
            <div>
              <div className="font-medium">Operation Failed</div>
              <div className="text-sm opacity-90">{error}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Info Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">What gets cleared?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-blue-500" />
                <span className="font-medium">Qdrant (Vector DB)</span>
              </div>
              <div className="text-sm text-muted-foreground pl-6">
                Document embeddings, search index, and vector representations
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-orange-500" />
                <span className="font-medium">MinIO (Object Storage)</span>
              </div>
              <div className="text-sm text-muted-foreground pl-6">
                Uploaded images, processed documents, and file metadata
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
