import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";

import "./globals.css";

import { AuthProvider } from "@/contexts/auth-context";
import { AuthGuard } from "@/components/auth-guard";

const fontSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Labour ERP",
  description: "Connected labour operations dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${fontSans.variable} font-sans antialiased`}>
        <AuthProvider>
          <AuthGuard>{children}</AuthGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
