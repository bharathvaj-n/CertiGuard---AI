'use client';

import React, { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import styles from './dashboard.module.css';
import { 
    Search, 
    Bell, 
    HelpCircle, 
    ChevronDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (typeof window !== 'undefined') {
       if (!localStorage.getItem('certiguard_token')) {
         router.replace('/login');
       }
    }
  }, [router]);

  const getPageTitle = () => {
    if (pathname === '/dashboard') return 'System Overview';
    if (pathname === '/dashboard/verify') return 'New Verification';
    if (pathname === '/dashboard/history') return 'Archive Registry';
    if (pathname.includes('/history/')) return 'Verification Audit';
    if (pathname === '/dashboard/analytics') return 'Intelligence Analytics';
    return 'Dashboard';
  };

  return (
    <div className={styles.layout}>
      <Sidebar />
      <main className={styles.main}>
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.pageIndicator}>
                <div className={styles.indicatorDot}></div>
                <span className={styles.pathTitle}>{getPageTitle()}</span>
            </div>
            <div className={styles.searchBar}>
                <Search size={16} color="#8b949e" />
                <input type="text" placeholder="Search across all records..." />
                <span className={styles.kbd}>⌘K</span>
            </div>
          </div>
          
          <div className={styles.headerRight}>
             <div className={styles.actionIcons}>
                <button className={styles.headerBtn} aria-label="Support">
                    <HelpCircle size={18} />
                </button>
                <button className={styles.headerBtn} aria-label="Notifications">
                    <Bell size={18} />
                    <span className={styles.badge}></span>
                </button>
             </div>
             
             <div className={styles.divider}></div>

             <div className={styles.profile}>
                <div className={styles.profileInfo}>
                    <span className={styles.name}>Admin User</span>
                    <span className={styles.role}>Institution Admin</span>
                </div>
                <div className={styles.avatar}>A</div>
                <ChevronDown size={14} color="#8b949e" />
             </div>
          </div>
        </header>

        <div className={styles.contentWrapper}>
            <AnimatePresence mode="wait">
                <motion.div 
                    key={pathname}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                    className={styles.content}
                >
                    {children}
                </motion.div>
            </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
