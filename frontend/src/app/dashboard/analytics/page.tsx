'use client';

import React, { useEffect, useState } from 'react';
import { Users, ShieldCheck, Activity } from 'lucide-react';
import styles from './analytics.module.css';

interface AnalyticsStats {
  total: number;
  genuine: number;
  suspicious: number;
  likely_fake: number;
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<AnalyticsStats>({ total: 0, genuine: 0, suspicious: 0, likely_fake: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const token = localStorage.getItem('certiguard_token');
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);
        const res = await fetch('http://localhost:8000/api/dashboard/stats', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          signal: controller.signal
        });
        clearTimeout(timeout);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch {
        // backend offline — fail silently
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  const total = stats.total || 0;
  const genuineRate = total > 0 ? ((stats.genuine / total) * 100).toFixed(1) : 0;
  const fraudRate = total > 0 ? (((stats.suspicious + stats.likely_fake) / total) * 100).toFixed(1) : 0;

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>System Analytics</h1>
        <p>Real-time data visualization of certificate verification patterns</p>
      </header>
      
      <div className={styles.metrics}>
        <div className={styles.metricCard}>
            <div className={styles.iconBox} style={{ backgroundColor: 'rgba(63, 185, 80, 0.1)' }}>
                <ShieldCheck size={20} color="#3fb950" />
            </div>
            <div className={styles.val}>{genuineRate}%</div>
            <div className={styles.lbl}>Authenticity Pass Rate</div>
        </div>
        <div className={styles.metricCard}>
            <div className={styles.iconBox} style={{ backgroundColor: 'rgba(88, 166, 255, 0.1)' }}>
                <Users size={20} color="#58a6ff" />
            </div>
            <div className={styles.val}>{stats.total}</div>
            <div className={styles.lbl}>Total Active Verifications</div>
        </div>
        <div className={styles.metricCard}>
            <div className={styles.iconBox} style={{ backgroundColor: 'rgba(248, 81, 73, 0.1)' }}>
                <Activity size={20} color="#f85149" />
            </div>
            <div className={styles.val}>{fraudRate}%</div>
            <div className={styles.lbl}>Fraud Detection Rate</div>
        </div>
      </div>

      <div className={styles.charts}>
        <div className={styles.chartWrapper}>
            <h3>Verification Integrity Distribution</h3>
            <div className={styles.barGraph}>
                <div className={styles.barItem}>
                    <div className={styles.label}>Genuine</div>
                    <div className={styles.track}>
                        <div className={styles.fill} style={{ width: `${genuineRate}%`, backgroundColor: '#3fb950' }}></div>
                    </div>
                </div>
                <div className={styles.barItem}>
                    <div className={styles.label}>Suspicious</div>
                    <div className={styles.track}>
                        <div className={styles.fill} style={{ width: `${total > 0 ? (stats.suspicious/total)*100 : 0}%`, backgroundColor: '#d29922' }}></div>
                    </div>
                </div>
                <div className={styles.barItem}>
                    <div className={styles.label}>Likely Fake</div>
                    <div className={styles.track}>
                        <div className={styles.fill} style={{ width: `${total > 0 ? (stats.likely_fake/total)*100 : 0}%`, backgroundColor: '#f85149' }}></div>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
