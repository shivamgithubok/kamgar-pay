"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/contexts/auth-context";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "ready" && !isAuthenticated && pathname !== "/login") {
      router.replace("/login");
    }
  }, [isAuthenticated, pathname, router, status]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="rounded-2xl border border-border bg-card px-8 py-6 text-center shadow-card">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Loading workspace</p>
          <p className="mt-2 text-lg font-semibold text-foreground">Checking authentication…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated && pathname !== "/login") {
    return null;
  }

  return <>{children}</>;
}
