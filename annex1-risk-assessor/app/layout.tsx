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
  title: "Annex 1 Intervention Risk Assessor (Portfolio)",
  description:
    "Portfolio demo app for aseptic intervention risk scoring aligned with EU GMP Annex 1 concepts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-slate-50 text-slate-900`}
      >
        <div className="flex min-h-screen flex-col">
          <main className="flex-1">{children}</main>
          <footer className="border-t border-slate-200 bg-white px-6 py-3 text-center text-sm font-semibold text-slate-700">
            Property of Mark Healy
          </footer>
        </div>
      </body>
    </html>
  );
}
