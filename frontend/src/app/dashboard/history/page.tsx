'use client';

import React, { useEffect, useState } from 'react';
import { 
    Search, 
    Filter, 
    ChevronRight, 
    Calendar,
    Trash2
} from 'lucide-react';
import { motion } from 'framer-motion';
import styles from './history.module.css';
import { useRouter } from 'next/navigation';

interface HistoryRecord {
  id: string;
  verification_id: string;
  candidate_name?: string;
  filename: string;
  status: string;
  risk_score: number;
  created_at: string;
  extracted_data?: {
    candidate_name?: string;
  };
}

export default function HistoryPage() {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('All');
  const router = useRouter();

  useEffect(() => {
    async function fetchHistory() {
        try {
            const token = localStorage.getItem('certiguard_token');
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000);
            const res = await fetch('http://localhost:8000/api/certificates/history', {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {},
                signal: controller.signal
            });
            clearTimeout(timeout);
            if (res.ok) {
                const data = await res.json();
                setRecords(data);
            }
        } catch {
            // backend offline — fail silently
        } finally {
            setLoading(false);
        }
    }
    fetchHistory();
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('🚨 SECURITY WARNING: This action will permanently remove this record and all associated forensic analysis data. Proceed anyway?')) return;
    
    try {
        const token = localStorage.getItem('certiguard_token');
        const res = await fetch(`http://localhost:8000/api/certificates/${id}`, {
            method: 'DELETE',
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (res.ok) {
            setRecords(prev => prev.filter(r => r.id !== id));
        } else {
            alert('Failed to delete record. Access denied or server error.');
        }
    } catch {
        alert('Network error: Could not reach verification server.');
    }
  };
  const filteredRecords = records.filter(r => {
    const matchesSearch = 
        r.verification_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.extracted_data?.candidate_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'All' || r.status === filterStatus;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusClass = (status: string) => {
    return status.toLowerCase().replace(' ', '');
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.titleArea}>
            <h1>Verification Archives</h1>
            <p>Access and audit lifetime verification records</p>
        </div>
        <div className={styles.statsMini}>
            <div className={styles.miniItem}>
                <span>Total Stored</span>
                <strong>{records.length}</strong>
            </div>
        </div>
      </header>

      <div className={styles.toolbar}>
        <div className={styles.searchWrapper}>
            <Search size={18} className={styles.searchIcon} />
            <input 
                type="text" 
                placeholder="Search by ID, name, or filename..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={styles.searchInput}
            />
        </div>
        <div className={styles.filters}>
            <div className={styles.filterGroup}>
                <Filter size={16} />
                <select 
                    value={filterStatus} 
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className={styles.statusSelect}
                >
                    <option value="All">All Statuses</option>
                    <option value="Genuine">Genuine</option>
                    <option value="Suspicious">Suspicious</option>
                    <option value="Likely Fake">Likely Fake</option>
                </select>
            </div>
        </div>
      </div>

      <div className={styles.tableCard}>
        <div className={styles.tableWrapper}>
            <table className={styles.table}>
                <thead>
                    <tr>
                        <th># ID Reference</th>
                        <th>Subject Name</th>
                        <th>File Identity</th>
                        <th>Integrity Status</th>
                        <th>Risk Score</th>
                        <th><Calendar size={14} /> Created</th>
                        <th className={styles.actionsHeader}>Audit</th>
                    </tr>
                </thead>
                <tbody>
                    {loading ? (
                        <tr><td colSpan={7} className={styles.tableLoading}>Accessing Secure Records...</td></tr>
                    ) : filteredRecords.length > 0 ? (
                        filteredRecords.map((r, idx) => (
                            <motion.tr 
                                key={r.id}
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.02 }}
                                onClick={() => router.push(`/dashboard/history/${r.id}`)}
                                className={styles.row}
                            >
                                <td className={styles.mono}>{r.verification_id}</td>
                                <td className={styles.nameCell}>{r.extracted_data?.candidate_name || "Unknown"}</td>
                                <td className={styles.filename}>{r.filename}</td>
                                <td>
                                    <span className={`${styles.badge} ${styles[getStatusClass(r.status)]}`}>
                                        {r.status}
                                    </span>
                                </td>
                                <td>
                                    <div className={styles.riskBadge} style={{ color: r.status === 'Genuine' ? '#3fb950' : r.status === 'Suspicious' ? '#d29922' : '#f85149' }}>
                                        {r.risk_score.toFixed(1)}%
                                    </div>
                                </td>
                                <td className={styles.dateCell}>{new Date(r.created_at).toLocaleDateString()}</td>
                                <td className={styles.actionsCell}>
                                    <button 
                                        onClick={(e) => handleDelete(e, r.id)} 
                                        className={styles.deleteBtn}
                                        title="Delete Record"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                    <div className={styles.divider}></div>
                                    <ChevronRight size={18} />
                                </td>
                            </motion.tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={7} className={styles.noResults}>
                                <div className={styles.emptyContent}>
                                    <Search size={40} />
                                    <p>No records found matching your criteria</p>
                                    <button onClick={() => { setSearchTerm(''); setFilterStatus('All'); }}>Clear All Filters</button>
                                </div>
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
      </div>
    </div>
  );
}

