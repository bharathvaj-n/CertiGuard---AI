'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
    LayoutDashboard, 
    FileUp, 
    History, 
    Settings, 
    LogOut, 
    ShieldCheck,
    BarChart3
} from 'lucide-react';
import styles from './sidebar.module.css';

const navItems = [
  { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { name: 'Verify New', icon: FileUp, path: '/dashboard/verify' },
  { name: 'History', icon: History, path: '/dashboard/history' },
  { name: 'Analytics', icon: BarChart3, path: '/dashboard/analytics' },
  { name: 'Settings', icon: Settings, path: '/dashboard/settings' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('certiguard_token');
    localStorage.removeItem('certiguard_user');
    router.push('/login');
  };

  return (
    <div className={styles.sidebar}>
      <div className={styles.logoContainer}>
        <ShieldCheck size={32} color="#58a6ff" />
        <span className={styles.logoName}>CertiGuard</span>
      </div>
      
      <nav className={styles.nav}>
        {navItems.map((item) => (
          <Link 
            key={item.path} 
            href={item.path}
            prefetch={true}
            className={`${styles.navItem} ${pathname === item.path ? styles.active : ''}`}
          >
            <item.icon size={20} className={styles.icon} />
            <span>{item.name}</span>
          </Link>
        ))}
      </nav>
      
      <div className={styles.footer}>
        <button onClick={handleLogout} className={styles.logoutBtn}>
          <LogOut size={20} className={styles.icon} />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
