import React, { useRef, useState } from 'react';
import { Upload, AlertTriangle } from 'lucide-react';

export function CorpusUpload({ environmentId, onUploadComplete }) {
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [conflicts, setConflicts] = useState([]);
  const [pendingFiles, setPendingFiles] = useState(null);

  const buildFormData = (files, collisionMode) => {
    const formData = new FormData();
    files.forEach((file) => {
      const filename = file.webkitRelativePath || file.name;
      formData.append('files', file, filename);
    });
    if (environmentId) {
      formData.append('environment_id', environmentId);
    }
    if (collisionMode) {
      formData.append('collision_mode', collisionMode);
    }
    return formData;
  };

  const uploadFiles = async (files, collisionMode = null) => {
    setIsUploading(true);
    setError(null);

    const formData = buildFormData(files, collisionMode);
    const response = await fetch('http://localhost:8000/api/corpus/upload', {
      method: 'POST',
      body: formData
    });

    if (response.status === 409) {
      const payload = await response.json();
      setConflicts(payload.detail.conflicts || []);
      setPendingFiles(files);
      setIsUploading(false);
      return;
    }

    if (!response.ok) {
      const payload = await response.json();
      if (payload.detail?.error === 'unsupported_files') {
        const allowed = (payload.detail.allowed_extensions || []).join(', ');
        const rejected = (payload.detail.unsupported_files || []).join(', ');
        setError(`Unsupported files: ${rejected}. Allowed: ${allowed}`);
      } else {
        setError(payload.detail?.error || 'Upload failed');
      }
      setIsUploading(false);
      return;
    }

    setConflicts([]);
    setPendingFiles(null);
    setIsUploading(false);
    if (onUploadComplete) onUploadComplete();
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;
    uploadFiles(files);
    event.target.value = '';
  };

  const handleResolveConflict = (mode) => {
    if (!pendingFiles) return;
    uploadFiles(pendingFiles, mode);
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <input
          type="file"
          ref={fileInputRef}
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />
        <input
          type="file"
          ref={folderInputRef}
          multiple
          webkitdirectory="true"
          directory="true"
          className="hidden"
          onChange={handleFileSelect}
        />

        <button
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border border-white/10 text-slate-300 hover:text-white hover:bg-white/5 transition-all"
          disabled={isUploading}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={14} />
          Upload Files
        </button>
        <button
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border border-white/10 text-slate-300 hover:text-white hover:bg-white/5 transition-all"
          disabled={isUploading}
          onClick={() => folderInputRef.current?.click()}
        >
          <Upload size={14} />
          Upload Folder
        </button>
      </div>

      {error && (
        <div className="mt-2 flex items-start gap-2 text-xs text-red-300">
          <AlertTriangle size={14} className="mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {conflicts.length > 0 && (
        <div className="absolute right-0 mt-2 w-72 bg-[#1a1b26] border border-white/10 rounded-xl shadow-2xl p-3 z-50">
          <div className="text-xs text-slate-300 mb-2">
            {conflicts.length} file conflict{conflicts.length > 1 ? 's' : ''} detected.
          </div>
          <div className="text-[11px] text-slate-500 mb-3 truncate">
            {conflicts.slice(0, 3).join(', ')}
            {conflicts.length > 3 ? '…' : ''}
          </div>
          <div className="flex items-center gap-2">
            <button
              className="flex-1 bg-white/5 hover:bg-white/10 text-slate-300 text-[10px] uppercase font-bold py-1 rounded-md transition-colors"
              onClick={() => handleResolveConflict('rename')}
            >
              Rename
            </button>
            <button
              className="flex-1 bg-red-500/20 hover:bg-red-500/30 text-red-200 text-[10px] uppercase font-bold py-1 rounded-md transition-colors"
              onClick={() => handleResolveConflict('overwrite')}
            >
              Overwrite
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
