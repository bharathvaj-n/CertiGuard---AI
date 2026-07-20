'use client';

import React, { useState, useEffect } from 'react';
import { Upload, File, X, Info, CheckCircle2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './verify.module.css';

const PENDING_KEY = 'certiguard_pending_analysis';

interface UploadData {
  file_id: string;
  filename: string;
  file_path: string;
}

export default function VerifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(0);
  const router = useRouter();

  // On mount: resume any pending analysis that was interrupted by a refresh
  useEffect(() => {
    const pending = sessionStorage.getItem(PENDING_KEY);
    if (pending) {
      const uploadData: UploadData = JSON.parse(pending);
      setLoading(true);
      setStep(2);
      runAnalyze(uploadData);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const getToken = () => localStorage.getItem('certiguard_token');

  const friendlyError = (err: unknown, status?: number): string => {
    if (err instanceof Error) {
      if (err.name === 'AbortError') return 'Request timed out. The server is taking too long — check History in a moment.';
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))
        return 'Cannot reach the backend server. Make sure it is running on port 8000.';
    }
    if (status === 401) return 'Session expired or not logged in. Please log in again.';
    if (status === 403) return 'Access denied. You do not have permission.';
    if (status === 404) return 'API endpoint not found. Check backend route configuration.';
    if (status === 413) return 'File is too large. Maximum allowed size is 10 MB.';
    if (status === 422) return 'Invalid request data sent to server.';
    if (status === 500) return err instanceof Error ? err.message : 'Internal server error. Check backend logs.';
    return err instanceof Error ? err.message : 'Unknown error occurred.';
  };

  const apiFetch = async (url: string, options: RequestInit, timeoutMs = 10000): Promise<Response> => {
    const token = getToken();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          ...(options.headers || {}),
        },
      });
      return res;
    } finally {
      clearTimeout(timer);
    }
  };

  const runAnalyze = async (uploadData: UploadData) => {
    try {
        const analyzeRes = await apiFetch(
          'http://localhost:8000/api/certificates/analyze',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(uploadData),
          },
          120000
        );

        if (!analyzeRes.ok) {
            const errBody = await analyzeRes.json().catch(() => ({}));
            throw Object.assign(
              new Error(errBody.detail || `Analysis failed`),
              { status: analyzeRes.status }
            );
        }
        const resultData = await analyzeRes.json();
        sessionStorage.removeItem(PENDING_KEY);
        setStep(3);
        setTimeout(() => router.push(`/dashboard/history/${resultData.id}`), 600);

    } catch (err: unknown) {
        sessionStorage.removeItem(PENDING_KEY);
        const status = (err as { status?: number }).status;
        setError(friendlyError(err, status));
        setLoading(false);
        setStep(0);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    // Frontend validations before hitting network
    const token = getToken();
    if (!token) {
      setError('You are not logged in. Please log in to verify certificates.');
      return;
    }
    const MAX_SIZE_MB = 10;
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File is too large. Maximum allowed size is ${MAX_SIZE_MB} MB.`);
      return;
    }
    const allowed = ['pdf', 'jpg', 'jpeg', 'png'];
    const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
    if (!allowed.includes(ext)) {
      setError(`File type ".${ext}" is not supported. Upload a PDF, JPG, or PNG.`);
      return;
    }

    setLoading(true);
    setError('');
    setStep(0);

    try {
        // Quick health check — fail fast with a clear message
        try {
          await apiFetch('http://localhost:8000/api/health', {}, 3000);
        } catch {
          throw new Error('Failed to fetch');
        }

        const formData = new FormData();
        formData.append('file', file);

        // Step 1 — Upload
        setStep(1);
        const uploadRes = await apiFetch(
          'http://localhost:8000/api/certificates/upload',
          { method: 'POST', body: formData }
        );
        if (!uploadRes.ok) {
            const errBody = await uploadRes.json().catch(() => ({}));
            throw Object.assign(
              new Error(errBody.detail || 'Upload failed'),
              { status: uploadRes.status }
            );
        }
        const uploadData: UploadData = await uploadRes.json();

        // Persist before analyze — survives a page refresh
        sessionStorage.setItem(PENDING_KEY, JSON.stringify(uploadData));

        // Step 2 — Analyze
        setStep(2);
        await runAnalyze(uploadData);

    } catch (err: unknown) {
        sessionStorage.removeItem(PENDING_KEY);
        const status = (err as { status?: number }).status;
        setError(friendlyError(err, status));
        setLoading(false);
        setStep(0);
    }
  };

  const STEPS = [
    "Preparing Document",
    "Uploading to Secure Vault",
    "Running OCR & Forensic Analysis (may take 15-30s)",
    "Generating Verification Report"
  ];

  const stepHint = [
    '',
    '',
    'OCR text extraction is CPU-intensive. Please wait...',
    'Almost done!'
  ];

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Verify New Certificate</h1>
        <p>Upload digital or scanned documents for institutional-grade forensic analysis</p>
      </header>

      <div className={styles.content}>
        <AnimatePresence mode="wait">
          {!loading ? (
            <motion.div 
              key="upload"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className={styles.uploadArea}
            >
              <div 
                className={`${styles.dropZone} ${dragging ? styles.dragging : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input')?.click()}
              >
                <input 
                  id="file-input" 
                  type="file" 
                  className={styles.hiddenInput} 
                  onChange={handleSelect}
                  accept=".pdf,.jpg,.jpeg,.png"
                />
                <div className={styles.dropZoneContent}>
                  <Upload size={48} color={dragging ? '#58a6ff' : '#8b949e'} />
                  {file ? (
                    <div className={styles.fileSelected}>
                      <File size={24} color="#58a6ff" />
                      <span>{file.name}</span>
                      <button 
                          onClick={(e) => { e.stopPropagation(); setFile(null); }}
                          className={styles.removeBtn}
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ) : (
                    <>
                      <h3>Select certificate for analysis</h3>
                      <p>Drop PDF or Image files here</p>
                    </>
                  )}
                </div>
              </div>

              {error && (
                <div className={styles.errorCard}>
                   <p className={styles.error}>{error}</p>
                   <button onClick={() => { sessionStorage.removeItem(PENDING_KEY); setError(''); setLoading(false); setStep(0); }} className={styles.retryBtn}>
                     Reset & Try Again
                   </button>
                </div>
              )}
              
              <button 
                  disabled={!file || loading} 
                  className={styles.analyzeBtn}
                  onClick={handleAnalyze}
              >
                 Start Professional Verification
              </button>
              
              <div className={styles.trustFooter}>
                <div className={styles.trustItem}>
                    <Info size={14} />
                    <span>Bank-level encryption</span>
                </div>
                <div className={styles.trustItem}>
                    <Info size={14} />
                    <span>GDPR Compliant</span>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="loading"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={styles.loadingState}
            >
                <div className={styles.spinnerWrapper}>
                    <div className={styles.spinner}></div>
                    <div className={styles.checkIcon}>
                        <CheckCircle2 size={32} color="#58a6ff" />
                    </div>
                </div>
                
                <div className={styles.stepper}>
                    {STEPS.map((s, i) => (
                        <div key={i} className={`${styles.step} ${i <= step ? styles.active : ''}`}>
                            <div className={styles.stepDot}></div>
                            <span>{s}</span>
                        </div>
                    ))}
                </div>

                {stepHint[step] && (
                    <p className={styles.stepHint}>{stepHint[step]}</p>
                )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
