"use client";

import { useState, useEffect } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings, Database, Server, Trash2, AlertTriangle, CheckCircle, Loader2, Shield, Zap, Sliders, Activity, HardDrive, FileText } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/components/ui/sonner";
import { ConfigurationPanel } from "@/components/configuration-panel";

type ActionType = "q" | "m" | "all";

const actions = [
  {
    id: "q" as ActionType,
    title: "Clear Vector Database",
    description: "Remove all document embeddings from Qdrant vector store",
    detailedDescription: "This action will permanently delete all document embeddings and search indices. You'll need to re-upload and re-index your documents.",
    icon: Database,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-200",
    buttonVariant: "secondary" as const,
    confirmTitle: "Clear Vector Database?",
    confirmMsg: "This will permanently delete all document embeddings from Qdrant. This action cannot be undone.",
    successMsg: "Vector database cleared successfully",
    severity: "medium" as const
  },
  {
    id: "m" as ActionType,
    title: "Clear Object Storage",
    description: "Remove all uploaded images from MinIO storage bucket",
    detailedDescription: "This action will delete all stored images and file uploads. Original documents will be lost and cannot be recovered.",
    icon: Server,
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-200",
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
    color: "text-red-600",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-300",
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
  const [systemHealth, setSystemHealth] = useState({
    qdrantStatus: "operational",
    minioStatus: "operational",
    lastCleared: null as string | null,
    totalOperations: 0
  });

  useEffect(() => {
    // Load system health/stats on mount
    const stats = {
      qdrantStatus: "operational",
      minioStatus: "operational", 
      lastCleared: localStorage.getItem("last_maintenance_action"),
      totalOperations: parseInt(localStorage.getItem("maintenance_operations") || "0")
    };
    setSystemHealth(stats);
  }, []);

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
      
      // Update stats
      const newTotal = systemHealth.totalOperations + 1;
      localStorage.setItem("maintenance_operations", newTotal.toString());
      localStorage.setItem("last_maintenance_action", new Date().toISOString());
      setSystemHealth(prev => ({
        ...prev,
        totalOperations: newTotal,
        lastCleared: new Date().toISOString()
      }));
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
      className="flex flex-col min-h-0 flex-1"
    >
      {/* Header */}
      <div className="space-y-4 mb-4 text-center relative">
        {/* Background decoration */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-20 w-32 h-32 bg-blue-200/20 rounded-full blur-xl" />
          <div className="absolute top-10 right-32 w-24 h-24 bg-purple-200/20 rounded-full blur-xl" />
        </div>
        
        <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent relative z-10">
          System Maintenance
        </h1>
        <p className="text-muted-foreground text-base sm:text-lg max-w-2xl mx-auto relative z-10">
          Manage your vector database, object storage, and runtime configuration
        </p>
      </div>

      {/* Tabs Container with Scroll */}
      <Tabs defaultValue="maintenance" className="flex-1 flex flex-col min-h-0">
        <TabsList className="w-full max-w-md mx-auto mb-4 bg-gradient-to-r from-blue-100/50 via-purple-100/50 to-cyan-100/50 border border-blue-200/50 h-14 rounded-full p-1 shadow-sm">
          <TabsTrigger 
            value="maintenance" 
            className="flex-1 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-300 rounded-full font-medium"
          >
            <Shield className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">Data Management</span>
            <span className="sm:hidden">Data</span>
          </TabsTrigger>
          <TabsTrigger 
            value="configuration" 
            className="flex-1 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-300 rounded-full font-medium"
          >
            <Sliders className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">Configuration</span>
            <span className="sm:hidden">Config</span>
          </TabsTrigger>
        </TabsList>

        {/* Maintenance Tab */}
        <TabsContent value="maintenance" className="flex-1 min-h-0 overflow-y-auto mt-0 custom-scrollbar pr-2">
          <div className="space-y-4 pb-4">

        {/* Actions Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {actions.map((action, index) => {
          const Icon = action.icon;
          const isLoading = loading[action.id];
          
          return (
            <motion.div
              key={action.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="py-1"
            >
              <Card className={`h-full flex flex-col group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 border ${action.borderColor} bg-gradient-to-br ${action.bgColor} backdrop-blur-sm`}>
                <CardHeader className="pb-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`inline-flex w-14 h-14 items-center justify-center rounded-2xl ${action.color} bg-white border-2 ${action.borderColor} group-hover:scale-110 transition-transform shadow-sm`}>
                      <Icon className="w-7 h-7" />
                    </div>
                    <Badge 
                      variant={action.severity === 'critical' ? 'destructive' : action.severity === 'high' ? 'secondary' : 'outline'}
                      className="text-xs font-medium"
                    >
                      {action.severity === 'critical' ? '🚨' : action.severity === 'high' ? '⚠️' : '⚡'}
                    </Badge>
                  </div>
                  <CardTitle className={`text-xl font-bold ${action.color} group-hover:opacity-80 transition-opacity`}>
                    {action.title}
                  </CardTitle>
                  <CardDescription className="text-base leading-relaxed mt-2">
                    {action.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0 flex-1 grid grid-rows-[1fr_auto] gap-4">
                  <div className="p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50">
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {action.detailedDescription}
                    </p>
                  </div>
                  
                  <Dialog open={dialogOpen === action.id} onOpenChange={(open) => setDialogOpen(open ? action.id : null)}>
                    <DialogTrigger asChild>
                      <Button
                        variant={action.buttonVariant}
                        disabled={isAnyLoading}
                        className={`w-full h-12 font-semibold rounded-full shadow-md hover:shadow-xl transition-all duration-300 hover:scale-105 ${
                          action.severity === 'critical' 
                            ? 'bg-red-600 hover:bg-red-700 text-white' 
                            : action.severity === 'high'
                            ? 'bg-orange-600 hover:bg-orange-700 text-white'
                            : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
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
                              Confirm {action.title}
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

        {/* Info Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <Card className="border border-blue-200/50 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 hover:shadow-lg transition-shadow duration-300">
            <CardHeader className="pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-white border-2 border-blue-200/50 shadow-sm">
                  <Database className="w-5 h-5 text-blue-500" />
                </div>
                <CardTitle className="text-lg font-bold">Qdrant Vector Database</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span className="text-muted-foreground">Document embeddings and vector representations</span>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span className="text-muted-foreground">Search indices for visual content retrieval</span>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span className="text-muted-foreground">AI-generated semantic understanding data</span>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border border-orange-200/50 bg-gradient-to-br from-orange-500/5 to-amber-500/5 hover:shadow-lg transition-shadow duration-300">
            <CardHeader className="pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-white border-2 border-orange-200/50 shadow-sm">
                  <Server className="w-5 h-5 text-orange-500" />
                </div>
                <CardTitle className="text-lg font-bold">MinIO Object Storage</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span className="text-muted-foreground">Original uploaded documents and images</span>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span className="text-muted-foreground">Processed file thumbnails and previews</span>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-1.5 flex-shrink-0"></div>
                  <span className="text-muted-foreground">File metadata and storage organization</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
          </div>
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="flex-1 min-h-0 mt-0 h-full">
          <div className="h-full flex flex-col">
            <ConfigurationPanel />
          </div>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
