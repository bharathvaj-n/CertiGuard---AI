'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from './login.module.css';
import { ShieldCheck, Lock, User } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || 'Invalid credentials');
      }

      const data = await res.json();
      localStorage.setItem('certiguard_token', data.access_token);
      localStorage.setItem('certiguard_user', JSON.stringify(data.user));

      router.push('/dashboard');
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes('Failed to fetch')) {
        setError('Cannot reach backend. Make sure it is running on port 8000.');
      } else {
        setError(err instanceof Error ? err.message : 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.loginCard}>
        <div className={styles.header}>
          <div className={styles.logo}>
            <ShieldCheck size={40} color="#58a6ff" />
          </div>
          <h1>CertiGuard AI</h1>
          <p>Secure Certificate Verification Portal</p>
        </div>
        
        <form onSubmit={handleLogin} className={styles.form}>
          <div className={styles.inputGroup}>
            <User size={20} className={styles.icon} />
            <input 
              type="text" 
              placeholder="Username" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div className={styles.inputGroup}>
            <Lock size={20} className={styles.icon} />
            <input 
              type="password" 
              placeholder="Password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          {error && <p className={styles.error}>{error}</p>}
          
          <button type="submit" disabled={loading} className={styles.submitBtn}>
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>
        
        <div className={styles.footer}>
          <p>Access restricted to authorized verification staff.</p>
        </div>
      </div>
    </div>
  );
}
