'use client';

import React, { useEffect, useRef, useState } from 'react';
import { 
    CheckCircle2, 
    AlertTriangle, 
    XCircle, 
    ArrowRight,
    TrendingUp,
    Shield,
    Activity,
    Search
} from 'lucide-react';
import { motion } from 'framer-motion';
import styles from './page.module.css';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface Stats {
  total: number;
  genuine: number;
  suspicious: number;
  likely_fake: number;
}

interface ActivityItem {
  id: string;
  status: string;
  candidate_name: string;
  created_at: string;
  verification_id: string;
  filename: string;
  risk_score: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({ total: 0, genuine: 0, suspicious: 0, likely_fake: 0 });
  const [recent, setRecent] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [backendDown, setBackendDown] = useState(false);
  const backendDownRef = useRef(false);
  const router = useRouter();

  const fetchData = async () => {
    try {
        const token = localStorage.getItem('certiguard_token');
        const headers: Record<string, string> = token ? { 'Authorization': `Bearer ${token}` } : {};
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);

        const [statsRes, recentRes] = await Promise.all([
            fetch('http://localhost:8000/api/dashboard/stats', { headers, signal: controller.signal }),
            fetch('http://localhost:8000/api/dashboard/recent', { headers, signal: controller.signal })
        ]);
        clearTimeout(timeout);

        if (statsRes.ok && recentRes.ok) {
            setStats(await statsRes.json());
            setRecent(await recentRes.json());
            backendDownRef.current = false;
            setBackendDown(false);
        }
    } catch {
        backendDownRef.current = true;
        setBackendDown(true);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Only auto-refresh when backend is reachable
    const interval = setInterval(() => {
      if (!backendDownRef.current) fetchData();
    }, 60000);
    return () => clearInterval(interval);
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = d.toDateString() === yesterday.toDateString();
    
    if (isToday) return 'Today';
    if (isYesterday) return 'Yesterday';
    return d.toLocaleDateString();
  };

  const StatusBadge = ({ status }: { status: string }) => {
    const s = status.toLowerCase().replace(' ', '');
    return (
        <span className={`${styles.badge} ${styles[s]}`}>
            {status}
        </span>
    );
  };

  const getRiskColor = (score: number, status: string) => {
    if (status === 'Genuine') return '#3fb950';
    if (status === 'Suspicious') return '#d29922';
    return '#f85149';
  };

  return (
    <div className={styles.container}>
      {backendDown && (
        <div className={styles.offlineBanner}>
          <span>⚠ Backend server is not running. Start it with:</span>
          <code>cd backend &amp;&amp; python -m uvicorn app.main:app --reload --port 8000</code>
          <button onClick={fetchData}>Retry</button>
        </div>
      )}
      <header className={styles.welcome}>
        <div className={styles.titleInfo}>
            <h1>Institutional Overview</h1>
            <p>Monitored: <span className={styles.activeLabel}>Live Detection Engine Active</span></p>
        </div>
        <div className={styles.actions}>
            <Link href="/dashboard/verify" className={styles.mainActionBtn}>
                <Shield size={18} /> New Verification
            </Link>
        </div>
      </header>

      <div className={styles.statsGrid}>
        {[
            { label: 'System Total', val: stats.total, icon: <Activity size={20} />, class: styles.total, sub: 'Lifetime analyzed' },
            { label: 'Genuine', val: stats.genuine, icon: <CheckCircle2 size={20} />, class: styles.genuine, sub: 'Passed all checks' },
            { label: 'Suspicious', val: stats.suspicious, icon: <AlertTriangle size={20} />, class: styles.suspicious, sub: 'Low data consistency' },
            { label: 'Likely Fake', val: stats.likely_fake, icon: <XCircle size={20} />, class: styles.fake, sub: 'Integrity compromised' },
        ].map((card, idx) => (
            <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`${styles.card} ${card.class}`}
            >
                <div className={styles.cardHeader}>
                    {card.icon}
                    <span>{card.label}</span>
                </div>
                <div className={styles.cardValue}>{loading ? '...' : card.val}</div>
                <p className={styles.cardSubtext}>{card.sub}</p>
            </motion.div>
        ))}
      </div>

      <div className={styles.mainContent}>
        <div className={styles.leftColumn}>
            <div className={styles.sectionHeader}>
                <div className={styles.shTitle}>
                    <Activity size={18} />
                    <h2>Live Activity</h2>
                </div>
                <Link href="/dashboard/history" className={styles.viewHistory}>
                    Manage Archives <ArrowRight size={14} />
                </Link>
            </div>

            <div className={styles.activityFeed}>
                {loading ? (
                    <div className={styles.emptyState}>Synchronizing with database...</div>
                ) : recent.length > 0 ? (
                    recent.map((item, idx) => (
                        <motion.div 
                            key={item.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className={styles.activityRow}
                            onClick={() => router.push(`/dashboard/history/${item.id}`)}
                        >
                            <div className={styles.actMain}>
                                <div className={styles.actIcon}>
                                    {item.status === 'Genuine' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                                </div>
                                <div className={styles.actInfo}>
                                    <div className={styles.actTop}>
                                        <strong>{item.candidate_name || 'Anonymous Subject'}</strong>
                                        <span className={styles.actDate}>{formatDate(item.created_at)}</span>
                                    </div>
                                    <span className={styles.actRef}>{item.verification_id} • {item.filename}</span>
                                </div>
                            </div>
                            <div className={styles.actSide}>
                                <div className={styles.actScore} style={{ color: getRiskColor(item.risk_score, item.status) }}>
                                    {item.risk_score.toFixed(1)}% Risk
                                </div>
                                <StatusBadge status={item.status} />
                            </div>
                        </motion.div>
                    ))
                ) : (
                    <div className={styles.emptyState}>
                        <Search size={40} />
                        <p>No recent verifications found.</p>
                        <Link href="/dashboard/verify">Analyze your first certificate</Link>
                    </div>
                )}
            </div>
        </div>

        <div className={styles.rightColumn}>
            <div className={styles.healthCard}>
                <div className={styles.hcHeader}>
                    <TrendingUp size={18} />
                    <h3>Engine Health</h3>
                </div>
                <div className={styles.hcList}>
                    <div className={styles.hcItem}>
                        <div className={styles.hcStatus} style={{ background: '#3fb950' }}></div>
                        <label>OCR Engine (EasyOCR)</label>
                        <span>Active</span>
                    </div>
                    <div className={styles.hcItem}>
                        <div className={styles.hcStatus} style={{ background: '#3fb950' }}></div>
                        <label>ML Scorer (Ensemble)</label>
                        <span>Optimal</span>
                    </div>
                    <div className={styles.hcItem}>
                        <div className={styles.hcStatus} style={{ background: '#3fb950' }}></div>
                        <label>Forensic Pipeline</label>
                        <span>Secure</span>
                    </div>
                </div>
            </div>

            <div className={styles.supportCard}>
                <h4>Need assistance?</h4>
                <p>Read our documentation on forensic score calculation or contact technical support.</p>
                <div className={styles.supportLinks}>
                    <a href="#">Guidelines</a>
                    <a href="#">API Docs</a>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
