"use client";

import Link from "next/link";
import { use, type FormEvent, useEffect, useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  Eye,
  FileCheck,
  FileCode,
  FileImage,
  FileText,
  HardHat,
  Plus,
  RefreshCw,
  Trash2,
  Upload,
  UserCheck,
  X,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  ApiError,
  deleteDocument,
  getDocumentDownloadUrl,
  getWorker,
  getWorkerDocuments,
  uploadWorkerDocument,
  type DocumentResponse,
  type WorkerDetailResponse,
} from "@/lib/api-client";

const DOCUMENT_TYPES = [
  "Aadhaar Card",
  "PAN Card",
  "Bank Passbook",
  "Labour Agreement",
  "Skill Certificate",
  "Other",
];

const ALLOWED_EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg"];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function getFileIcon(mimeType: string) {
  if (mimeType.includes("pdf")) {
    return <FileText className="h-4 w-4 text-rose-500" />;
  }
  if (mimeType.includes("image")) {
    return <FileImage className="h-4 w-4 text-emerald-500" />;
  }
  return <FileCode className="h-4 w-4 text-sky-500" />;
}

export default function WorkerDocumentsPage({ params }: { params: Promise<{ workerId: string }> }) {
  const { workerId } = use(params);

  const [worker, setWorker] = useState<WorkerDetailResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState("Aadhaar Card");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  // Fetch worker info & documents
  useEffect(() => {
    const loadWorkerData = async () => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const [workerRes, docsRes] = await Promise.all([
          getWorker(workerId).catch(() => null),
          getWorkerDocuments(workerId),
        ]);

        if (workerRes) {
          setWorker(workerRes);
        } else {
          setWorker({
            id: workerId,
            organization_id: "",
            worker_code: "WRK-" + workerId.slice(0, 6),
            first_name: "Worker Profile",
            name: "Worker Profile",
            default_wage_rate: "0",
            status: "active",
            joined_on: new Date().toISOString().slice(0, 10),
          });
        }

        setDocuments(docsRes.items);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "Failed to load worker documents.");
      } finally {
        setLoading(false);
      }
    };

    void loadWorkerData();
  }, [workerId, refreshToken]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null);
    setUploadSuccess(null);
    const file = e.target.files?.[0];

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setUploadError(`Invalid format '${ext}'. Allowed file types: PDF, PNG, JPG`);
      setSelectedFile(null);
      e.target.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setUploadError(`File size (${(file.size / (1024 * 1024)).toFixed(2)}MB) exceeds 10MB limit.`);
      setSelectedFile(null);
      e.target.value = "";
      return;
    }

    setSelectedFile(file);
  };

  const handleUploadSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError("Please select a file to upload.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      await uploadWorkerDocument(workerId, selectedDocType, selectedFile);
      setUploadSuccess(`Successfully uploaded '${selectedFile.name}'`);
      setSelectedFile(null);
      setShowUploadModal(false);
      setRefreshToken((val) => val + 1);
    } catch (error) {
      setUploadError(error instanceof ApiError ? error.message : "File upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string, fileName: string) => {
    if (!confirm(`Are you sure you want to delete '${fileName}'?`)) return;
    setDeletingId(docId);
    try {
      await deleteDocument(docId);
      setRefreshToken((val) => val + 1);
    } catch (error) {
      alert(error instanceof ApiError ? error.message : "Could not delete document.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <AppShell activePath="/workers">
      <div className="space-y-6">
        {/* Navigation Back Link */}
        <div className="flex items-center gap-3">
          <Button asChild size="sm" variant="outline">
            <Link href="/workers">
              <ArrowLeft className="h-4 w-4" />
              Back to Workers
            </Link>
          </Button>
        </div>

        {/* Worker Summary Banner */}
        {worker ? (
          <div className="rounded-2xl border border-border/80 bg-card p-6 shadow-card">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-labour-amber text-labour-ink font-bold text-xl">
                  <HardHat className="h-7 w-7" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-2xl font-black text-foreground">
                      {worker.name || `${worker.first_name} ${worker.last_name || ""}`.trim()}
                    </h2>
                    <StatusPill value={worker.status} />
                  </div>
                  <div className="mt-1 flex flex-wrap gap-4 text-xs font-semibold text-muted-foreground">
                    <span>Code: <strong className="text-foreground">{worker.worker_code}</strong></span>
                    <span>Trade: <strong className="text-foreground">{worker.trade || "General Worker"}</strong></span>
                    {worker.assigned_site_name ? (
                      <span>Site: <strong className="text-foreground">{worker.assigned_site_name}</strong></span>
                    ) : null}
                  </div>
                </div>
              </div>

              <Button onClick={() => setShowUploadModal(true)}>
                <Plus className="h-4 w-4" />
                Upload Document
              </Button>
            </div>
          </div>
        ) : null}

        <PageHeader
          eyebrow="Worker Identity & KYC"
          title="Worker Documents"
          description="Manage compliance records, identification identity proof, passbooks, contracts, and certificates."
        />

        {/* Upload Alert Notification */}
        {uploadSuccess ? (
          <div className="flex items-center justify-between rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
            <div className="flex items-center gap-2 font-semibold">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              {uploadSuccess}
            </div>
            <button type="button" onClick={() => setUploadSuccess(null)}>
              <X className="h-4 w-4 text-emerald-600" />
            </button>
          </div>
        ) : null}

        {/* Upload Modal Dialog */}
        {showUploadModal ? (
          <Card className="animate-fade-up overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Upload Worker Document</CardTitle>
                <CardDescription>Upload identity cards, agreements, passbooks, or certificates.</CardDescription>
              </div>
              <Button size="sm" variant="ghost" onClick={() => setShowUploadModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleUploadSubmit}>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">Document Type *</label>
                  <select
                    required
                    className="h-10 w-full rounded-xl border border-input bg-background px-3.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={selectedDocType}
                    onChange={(e) => setSelectedDocType(e.target.value)}
                  >
                    {DOCUMENT_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-muted-foreground">
                    File Attachment * (PDF, PNG, JPG - Max 10MB)
                  </label>
                  <Input
                    required
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    className="cursor-pointer"
                    onChange={handleFileChange}
                  />
                  {selectedFile ? (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Selected: <strong className="text-foreground">{selectedFile.name}</strong> ({formatBytes(selectedFile.size)})
                    </p>
                  ) : null}
                </div>

                {uploadError ? (
                  <p className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {uploadError}
                  </p>
                ) : null}

                <div className="flex gap-3 pt-2">
                  <Button disabled={uploading || !selectedFile} type="submit">
                    <Upload className="h-4 w-4" />
                    {uploading ? "Uploading..." : "Start Upload"}
                  </Button>
                  <Button disabled={uploading} type="button" variant="outline" onClick={() => setShowUploadModal(false)}>
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        ) : null}

        {/* Documents Directory Table */}
        <Card className="animate-fade-up overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Document Vault</CardTitle>
              <CardDescription>All records registered to this worker account.</CardDescription>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setRefreshToken((val) => val + 1)}>
              <RefreshCw className="h-4 w-4" />
              Refresh List
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="animate-pulse rounded-2xl border border-border bg-card/70 p-4 text-sm text-muted-foreground">
                Loading documents...
              </div>
            ) : null}

            {errorMessage ? (
              <div className="flex flex-col gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
                <span>{errorMessage}</span>
                <button
                  className="font-bold underline underline-offset-4"
                  onClick={() => setRefreshToken((v) => v + 1)}
                  type="button"
                >
                  Try again
                </button>
              </div>
            ) : null}

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>File Name</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Uploaded Date</TableHead>
                  <TableHead>Uploaded By</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && documents.length === 0 ? (
                  <TableRow>
                    <TableCell className="h-28 text-center text-muted-foreground" colSpan={6}>
                      No documents stored for this worker yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  documents.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell>
                        <span className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-xs font-semibold text-secondary-foreground">
                          {doc.document_type}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 font-medium text-foreground">
                          {getFileIcon(doc.mime_type)}
                          <span>{doc.original_file_name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatBytes(doc.file_size)}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                        {doc.created_at ? doc.created_at.slice(0, 10) : "N/A"}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {doc.uploaded_by_name}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button asChild size="sm" variant="outline" className="h-8">
                            <a href={getDocumentDownloadUrl(doc.id)} target="_blank" rel="noopener noreferrer" title="View / Preview">
                              <Eye className="h-3.5 w-3.5" />
                              View
                            </a>
                          </Button>
                          <Button asChild size="sm" variant="ghost" className="h-8">
                            <a href={getDocumentDownloadUrl(doc.id)} download={doc.original_file_name} title="Download File">
                              <Download className="h-3.5 w-3.5" />
                            </a>
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                            disabled={deletingId === doc.id}
                            onClick={() => handleDelete(doc.id, doc.original_file_name)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {!showUploadModal && !loading && !errorMessage && documents.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-card/60 p-8 text-center text-sm text-muted-foreground">
            No compliance or identity documents found for this worker profile.
            <div className="mt-4">
              <Button onClick={() => setShowUploadModal(true)}>
                <Plus className="h-4 w-4" />
                Upload First Document
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
