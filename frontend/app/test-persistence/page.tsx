"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSearchStore, useChatStore, useUploadStore } from "@/stores/app-store";
import { Badge } from "@/components/ui/badge";
import { Eye, Brain, CloudUpload, RotateCcw } from "lucide-react";

export default function TestPersistencePage() {
  const searchStore = useSearchStore();
  const chatStore = useChatStore();
  const uploadStore = useUploadStore();

  const addTestSearchData = () => {
    searchStore.setQuery("test document search");
    searchStore.setResults([
      { 
        image_url: "https://via.placeholder.com/300x200",
        label: "Test Document 1",
        score: 0.95,
        payload: {}
      },
      { 
        image_url: "https://via.placeholder.com/300x200", 
        label: "Test Document 2",
        score: 0.87,
        payload: {}
      }
    ], 1234);
    searchStore.setHasSearched(true);
  };

  const addTestChatData = () => {
    chatStore.addMessage({
      id: "test-user-1",
      role: "user",
      content: "What's in my documents?"
    });
    chatStore.addMessage({
      id: "test-assistant-1", 
      role: "assistant",
      content: "I found several interesting documents in your collection. Here's what I discovered..."
    });
  };

  const simulateUpload = () => {
    uploadStore.setUploading(true);
    uploadStore.setProgress(25);
    uploadStore.setStatusText("Processing documents...");
    uploadStore.setJobId("test-job-123");
  };

  const clearAllData = () => {
    searchStore.reset();
    chatStore.reset();
    uploadStore.reset();
  };

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Test Data Persistence</h1>
        <p className="text-muted-foreground">
          Test the persistence functionality by adding sample data, navigating away, and returning.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Search Test */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-blue-500" />
              Search Data
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Current query: <Badge variant="outline">{searchStore.query || "None"}</Badge>
              </p>
              <p className="text-sm text-muted-foreground">
                Results: <Badge variant="outline">{searchStore.results.length}</Badge>
              </p>
              <p className="text-sm text-muted-foreground">
                Has searched: <Badge variant={searchStore.hasSearched ? "default" : "outline"}>
                  {searchStore.hasSearched ? "Yes" : "No"}
                </Badge>
              </p>
            </div>
            <Button onClick={addTestSearchData} className="w-full">
              Add Test Search Data
            </Button>
          </CardContent>
        </Card>

        {/* Chat Test */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              Chat Data
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Messages: <Badge variant="outline">{chatStore.messages.length}</Badge>
              </p>
              <p className="text-sm text-muted-foreground">
                Tool calling: <Badge variant={chatStore.toolCallingEnabled ? "default" : "outline"}>
                  {chatStore.toolCallingEnabled ? "Enabled" : "Disabled"}
                </Badge>
              </p>
              <p className="text-sm text-muted-foreground">
                K value: <Badge variant="outline">{chatStore.k}</Badge>
              </p>
            </div>
            <Button onClick={addTestChatData} className="w-full">
              Add Test Chat Data
            </Button>
          </CardContent>
        </Card>

        {/* Upload Test */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CloudUpload className="w-5 h-5 text-green-500" />
              Upload Data
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Uploading: <Badge variant={uploadStore.uploading ? "default" : "outline"}>
                  {uploadStore.uploading ? "Yes" : "No"}
                </Badge>
              </p>
              <p className="text-sm text-muted-foreground">
                Progress: <Badge variant="outline">{uploadStore.uploadProgress}%</Badge>
              </p>
              <p className="text-sm text-muted-foreground">
                Status: <Badge variant="outline">{uploadStore.statusText || "None"}</Badge>
              </p>
              <p className="text-sm text-muted-foreground">
                Job ID: <Badge variant="outline">{uploadStore.jobId || "None"}</Badge>
              </p>
            </div>
            <Button onClick={simulateUpload} className="w-full">
              Simulate Upload
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card className="border-2 border-dashed">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <h3 className="text-lg font-semibold">Test Instructions</h3>
            <ol className="text-sm text-muted-foreground space-y-2 text-left max-w-md mx-auto">
              <li>1. Click the buttons above to add test data</li>
              <li>2. Navigate to different pages using the nav bar</li>
              <li>3. Return to those pages to see the data persisted</li>
              <li>4. Check the nav bar for data indicators</li>
              <li>5. Look for "data restored" banners on the pages</li>
            </ol>
            <Button onClick={clearAllData} variant="outline" className="mt-4">
              <RotateCcw className="w-4 h-4 mr-2" />
              Clear All Test Data
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
