'use client';

import React, { useState } from 'react';
import { Save, Shield, Database, Bell } from 'lucide-react';
import styles from './settings.module.css';

export default function SettingsPage() {
  const [threshold, setThreshold] = useState(80);
  
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>System Configuration</h1>
        <p>Global parameters for detection scoring and verification</p>
      </header>
      
      <div className={styles.grid}>
        <div className={styles.section}>
            <div className={styles.sectionHeader}>
                <Shield size={20} />
                <h2>Detection Parameters</h2>
            </div>
            <div className={styles.formGroup}>
                <label>Authenticity Threshold ({threshold}%)</label>
                <input 
                    type="range" 
                    min="0" max="100" 
                    value={threshold} 
                    onChange={(e) => setThreshold(parseInt(e.target.value))} 
                />
                <p className={styles.info}>Certificates below this score will be marked Suspicious.</p>
            </div>
            <div className={styles.toggleGroup}>
                <label>Deep Image Forensic Check</label>
                <input type="checkbox" defaultChecked />
            </div>
            <button className={styles.saveBtn}><Save size={18} /> Save Settings</button>
        </div>

        <div className={styles.section}>
            <div className={styles.sectionHeader}>
                <Database size={20} />
                <h2>Verification Database</h2>
            </div>
            <div className={styles.dbActions}>
                <button>Sync with Central DB</button>
                <button>Clear Verification Cache</button>
                <button className={styles.danger}>Wipe Mock Records</button>
            </div>
        </div>

        <div className={styles.section}>
            <div className={styles.sectionHeader}>
                <Bell size={20} />
                <h2>Notifications</h2>
            </div>
            <div className={styles.toggleGroup}>
                <label>Email on Critical Fraud Detection</label>
                <input type="checkbox" defaultChecked />
            </div>
            <div className={styles.toggleGroup}>
                <label>Daily Verification Summary</label>
                <input type="checkbox" />
            </div>
        </div>
      </div>
    </div>
  );
}
