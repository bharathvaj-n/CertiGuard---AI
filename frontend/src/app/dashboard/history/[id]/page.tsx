'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { 
    CheckCircle, 
    ShieldAlert, 
    XCircle, 
    ArrowLeft, 
    Download, 
    Calendar,
    Hash,
    User,
    Building2,
    CheckCircle2
} from 'lucide-react';
import { motion } from 'framer-motion';
import styles from './detail.module.css';
import Link from 'next/link';

interface ExtractedData {
  certificate_id: string;
  issue_date: string;
  candidate_name: string;
  issuer_name: string;
  ocr_confidence: number;
}

interface VerificationRecord {
  id: string;
  verification_id: string;
  created_at: string;
  status: string;
  risk_score: number;
  extracted_data?: ExtractedData;
  reasons: string[];
}

export default function VerificationDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params.id;
  const [result, setResult] = useState<VerificationRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchRecord() {
        try {
            const token = localStorage.getItem('certiguard_token');
            const res = await fetch(`http://localhost:8000/api/certificates/${id}`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (!res.ok) throw new Error('Verification record not found');
            const data = await res.json();
            setResult(data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Unknown error occurred');
        } finally {
            setLoading(false);
        }
    }
    if (id) fetchRecord();
  }, [id]);

  if (loading) return <div className={styles.loading}>Analyzing Record Data...</div>;
  if (error || !result) return <div className={styles.error}>Error: {error}</div>;

  return (
    <div className={styles.container}>
      <div className={styles.topNav}>
        <button onClick={() => router.back()} className={styles.backBtn}>
            <ArrowLeft size={18} /> Back
        </button>
        <div className={styles.meta}>
            <span className={styles.refId}>Reference: {result.verification_id}</span>
            <span className={styles.timestamp}>Analysis Date: {new Date(result.created_at).toLocaleString()}</span>
        </div>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className={styles.mainCard}
      >
        <div className={styles.resHeader}>
            <div className={styles.statusDisplay}>
                {result.status === "Genuine" ? (
                    <CheckCircle size={64} className={styles.iconGenuine} />
                ) : result.status === "Suspicious" ? (
                    <ShieldAlert size={64} className={styles.iconSuspicious} />
                ) : (
                    <XCircle size={64} className={styles.iconFake} />
                )}
                <div className={styles.statusText}>
                    <span className={styles.statusLabel}>Integrity Status</span>
                    <h2>{result.status}</h2>
                </div>
            </div>
            
            <div className={styles.riskMeterSection}>
                <div className={styles.meterInfo}>
                    <span>AI Risk Assessment</span>
                    <strong>{result.risk_score.toFixed(1)}%</strong>
                </div>
                <div className={styles.meterTrack}>
                    <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${result.risk_score}%` }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                        className={styles.meterFill} 
                        style={{ 
                            backgroundColor: result.status === "Genuine" ? '#3fb950' : result.status === "Suspicious" ? '#d29922' : '#f85149'
                        }}
                    ></motion.div>
                </div>
                <p className={styles.meterDescription}>
                    Based on 12+ forensic and text-based metrics
                </p>
            </div>
        </div>

        {result.extracted_data?.candidate_name && (
            <div className={styles.certBanner}>
                <span className={styles.issuerRow}>
                    <Building2 size={16} /> {result.extracted_data.issuer_name || "Official Issuer"}
                </span>
                <div className={styles.subjectRow}>
                    <User size={24} /> 
                    <div className={styles.subjectInfo}>
                        <p>Subject Name</p>
                        <h3>{result.extracted_data.candidate_name}</h3>
                    </div>
                </div>
            </div>
        )}

        <div className={styles.resGrid}>
            <div className={styles.resInfo}>
                <div className={styles.sectionHeader}>
                    <h3>Resource Mapping</h3>
                    <p>Fields extracted via OCR & Advanced Layout Analysis</p>
                </div>
                <div className={styles.infoTable}>
                    <div className={styles.dataPoint}>
                        <div className={styles.dpIcon}><Hash size={16}/></div>
                        <div className={styles.dpContent}>
                            <label>Certificate Code</label>
                            <span>{result.extracted_data?.certificate_id || "N/A"}</span>
                        </div>
                    </div>
                    <div className={styles.dataPoint}>
                        <div className={styles.dpIcon}><Calendar size={16}/></div>
                        <div className={styles.dpContent}>
                            <label>Issuance Date</label>
                            <span>{result.extracted_data?.issue_date || "N/A"}</span>
                        </div>
                    </div>
                    <div className={styles.dataPoint}>
                        <div className={styles.dpIcon}><CheckCircle2 size={16}/></div>
                        <div className={styles.dpContent}>
                            <label>OCR Confidence</label>
                            <span>{(result.extracted_data?.ocr_confidence ? result.extracted_data.ocr_confidence * 100 : 0).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className={styles.resInsights}>
                <div className={styles.sectionHeader}>
                    <h3>AI Explanations</h3>
                    <p>Contextual breakdown of the risk markers found</p>
                </div>
                <ul className={styles.insightList}>
                    {result.reasons?.length > 0 ? (
                        result.reasons.map((r: string, i: number) => (
                            <li key={i} className={r.includes('passed') ? styles.insightPos : styles.insightNeg}>
                                {r}
                            </li>
                        ))
                    ) : (
                        <li className={styles.insightNeutral}>No detailed explanation provided.</li>
                    )}
                </ul>
            </div>
        </div>
        
        <div className={styles.actions}>
            <button 
                className={styles.downloadBtn} 
                onClick={async () => {
                   const token = localStorage.getItem('certiguard_token');
                   const res = await fetch(`http://localhost:8000/api/certificates/${result.id}/report`, {
                       headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                   });
                   if (res.ok) {
                       const blob = await res.blob();
                       const url = window.URL.createObjectURL(blob);
                       const a = document.createElement('a');
                       a.href = url;
                       a.download = `Forensic_Report_${result.verification_id}.pdf`;
                       a.click();
                   } else {
                       alert('Failed to generate report');
                   }
                }}
            >
                <Download size={18} /> Export Forensic Report
            </button>
            <Link href="/dashboard/verify" className={styles.verifyNewBtn}>
                Verify New Document
            </Link>
        </div>
      </motion.div>
    </div>
  );
}
