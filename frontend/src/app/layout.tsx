import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CertiGuard AI",
  description: "Secure Certificate Verification Portal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.addEventListener('unhandledrejection', (e) => {
                if (e.reason?.message?.includes('MetaMask') || e.reason?.stack?.includes('extension')) {
                  e.stopPropagation();
                  e.preventDefault();
                }
              });
            `,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
