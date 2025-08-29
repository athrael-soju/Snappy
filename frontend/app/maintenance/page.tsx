"use client";

import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Button } from "@/components/ui/8bit/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/8bit/card";
import { Badge } from "@/components/ui/8bit/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/8bit/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/8bit/dialog";
import { Settings, Database, Server, Trash2, AlertTriangle, CheckCircle, Loader2, Shield, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

type ActionType = "q" | "m" | "all";

const actions = [
  {
    id: "q" as ActionType,
    title: "Clear Vector DB",
    description: "Remove all document embeddings from Qdrant vector store",
    detailedDescription: "This action will permanently delete all document embeddings and search indices. You'll need to re-upload and re-index your documents.",
    icon: Database,
    color: "text-primary",
    bgColor: "bg-primary/10",
    borderColor: "border-border",
    buttonVariant: "secondary" as const,
    confirmTitle: "Clear Vector Database?",
    confirmMsg: "This will permanently delete all document embeddings from Qdrant. This action cannot be undone.",
    successMsg: "Vector database cleared successfully",
    severity: "medium" as const
  },
  {
    id: "m" as ActionType,
    title: "Clear Object Store",
    description: "Remove all uploaded images from MinIO storage bucket",
    detailedDescription: "This action will delete all stored images and file uploads. Original documents will be lost and cannot be recovered.",
    icon: Server,
    color: "text-accent",
    bgColor: "bg-accent/10",
    borderColor: "border-border",
    buttonVariant: "destructive" as const,
    confirmTitle: "Clear Object Storage?",
    confirmMsg: "This will permanently delete all uploaded files and images from MinIO storage. This action cannot be undone and will affect all visual search functionality.",
    successMsg: "Object storage cleared successfully",
    severity: "high" as const
  },
  {
    id: "all" as ActionType,
    title: "Clear Everything",
    description: "Complete system reset - removes ALL data from both systems",
    detailedDescription: "This is a complete system reset that will delete all documents, embeddings, images, and search indices. The system will return to its initial empty state.",
    icon: Trash2,
    color: "text-destructive",
    bgColor: "bg-destructive/10",
    borderColor: "border-border",
    buttonVariant: "destructive" as const,
    confirmTitle: "Complete System Reset?",
    confirmMsg: "⚠️ DANGER: This will permanently delete ALL data from both Qdrant and MinIO. This includes all documents, embeddings, images, and search indices. This action cannot be undone and will reset the entire system to its initial state.",
    successMsg: "System completely reset",
    severity: "critical" as const
  }
];

export default function MaintenancePage() {
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<{ q: boolean; m: boolean; all: boolean }>({ q: false, m: false, all: false });
  const [dialogOpen, setDialogOpen] = useState<ActionType | null>(null);

  async function run(action: ActionType) {
    const actionConfig = actions.find(a => a.id === action);
    if (!actionConfig) return;

    setError(null);
    setStatus("");
    setLoading((s) => ({ ...s, [action]: true }));
    setDialogOpen(null); // Close dialog
    
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
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-red-500/10 to-orange-500/10 rounded-lg border border-red-500/20">
            <Shield className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">System Maintenance</h1>
            <p className="text-muted-foreground text-lg">Manage your vector database and object storage with care</p>
          </div>
        </div>
        
        {/* Quick Info */}
        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span>Destructive operations ahead</span>
          </div>
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-green-500" />
            <span>Confirm before proceeding</span>
          </div>
        </div>
      </div>

      {/* Warning Banner */}
      <Alert className="border-2 border-amber-200 bg-gradient-to-r from-amber-50/50 to-orange-50/50">
        <AlertTriangle className="h-5 w-5 text-amber-600" />
        <AlertTitle className="text-amber-800 font-semibold">⚠️ Destructive Operations</AlertTitle>
        <AlertDescription className="text-amber-700">
          The actions below permanently delete data and <strong>cannot be undone</strong>
        </AlertDescription>
      </Alert>

      {/* Actions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
              <Card className={`h-full flex flex-col group hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border-2 ${action.borderColor}`}>
                <CardHeader className="pb-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`inline-flex w-12 h-12 items-center justify-center rounded-xl ${action.color} ${action.bgColor} border ${action.borderColor} group-hover:scale-110 transition-transform`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <Badge 
                      variant={action.severity === 'critical' ? 'destructive' : action.severity === 'high' ? 'secondary' : 'outline'}
                      className="text-xs"
                    >
                      {action.severity === 'critical' ? '🚨 Critical' : action.severity === 'high' ? '⚠️ High Risk' : '⚡ Medium Risk'}
                    </Badge>
                  </div>
                  <CardTitle className={`text-xl font-bold ${action.color} group-hover:opacity-90 transition-opacity`}>
                    {action.title}
                  </CardTitle>
                  <CardDescription className="text-base leading-relaxed">
                    {action.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0 flex-1 grid grid-rows-[1fr_auto] gap-4">
                  <div className="p-3 bg-muted/30 rounded-lg">
                    <p className="text-sm text-muted-foreground">
                      {action.detailedDescription}
                    </p>
                  </div>
                  
                  <Dialog open={dialogOpen === action.id} onOpenChange={(open) => setDialogOpen(open ? action.id : null)}>
                    <DialogTrigger asChild>
                      <Button
                        variant={action.buttonVariant}
                        disabled={isAnyLoading}
                        className={`w-full h-12 font-semibold ${
                          action.severity === 'critical' 
                            ? 'bg-red-600 hover:bg-red-700 text-white' 
                            : action.severity === 'high'
                            ? 'bg-orange-600 hover:bg-orange-700 text-white'
                            : ''
                        }`}
                        size="lg"
                      >
                        {isLoading ? (
                          <>
                            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          <>
                            <Icon className="w-5 h-5 mr-2" />
                            {action.title}
                          </>
                        )}
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-md">
                      <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-lg">
                          <Icon className={`w-5 h-5 ${action.color}`} />
                          {action.confirmTitle}
                        </DialogTitle>
                        <DialogDescription className="text-base leading-relaxed pt-2">
                          {action.confirmMsg}
                        </DialogDescription>
                      </DialogHeader>
                      <div className="bg-muted/50 p-4 rounded-lg border-l-4 border-amber-400">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                          <p className="text-sm text-muted-foreground">
                            <strong>Important:</strong> This operation cannot be reversed. Make sure you have backups if needed.
                          </p>
                        </div>
                      </div>
                      <DialogFooter className="gap-2">
                          <Button 
                            variant="outline" 
                            onClick={() => setDialogOpen(null)}
                            disabled={isLoading}
                          >
                            Cancel
                          </Button>
                          <Button 
                            variant={action.buttonVariant}
                            onClick={() => run(action.id)}
                            disabled={isLoading}
                          className={action.severity === 'critical' ? 'bg-red-600 hover:bg-red-700' : action.severity === 'high' ? 'bg-orange-600 hover:bg-orange-700' : ''}
                          >
                            {isLoading ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Processing...
                              </>
                            ) : (
                              <>
                                <Icon className="w-4 h-4 mr-2" />
                              Confirm
                              </>
                            )}
                          </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
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
          >
            <Alert variant="default">
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Operation Completed</AlertTitle>
              <AlertDescription>{status}</AlertDescription>
            </Alert>
          </motion.div>
        )}
        
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Operation Failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Info Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-blue-200/50">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-500" />
              <CardTitle className="text-lg">Qdrant Vector Database</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">Document embeddings and vector representations</span>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">Search indices for visual content retrieval</span>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">AI-generated semantic understanding data</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-orange-200/50">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-orange-500" />
              <CardTitle className="text-lg">MinIO Object Storage</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">Original uploaded documents and images</span>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">Processed file thumbnails and previews</span>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-muted-foreground">File metadata and storage organization</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}
