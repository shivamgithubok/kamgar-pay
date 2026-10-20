"use client";

import Link from "next/link";
import { Bell, Menu, Search } from "lucide-react";
import { useState } from "react";

import { AppSidebar } from "@/components/app-sidebar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/auth-context";
import { navItems } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

type AppShellProps = {
  children: React.ReactNode;
  activePath?: string;
};

export function AppShell({ children, activePath }: AppShellProps) {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1480px] gap-5 px-4 py-4 sm:px-6">
      <AppSidebar activePath={activePath} />
      <main className="min-w-0 flex-1">
        <div className="mb-5 flex items-center gap-3 rounded-[1.5rem] bg-white/80 px-4 py-3 shadow-card">
          <button className="rounded-full p-2 text-muted-foreground hover:bg-muted lg:hidden" onClick={() => setOpen((value) => !value)} type="button" aria-label="Open navigation">
            <Menu className="h-5 w-5" />
          </button>
          <div className="relative min-w-0 flex-1">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input className="bg-muted/80 pl-10" placeholder="Search workers, sites, payroll..." />
          </div>
          <Button variant="outline" size="icon" aria-label="Notifications">
            <Bell className="h-4 w-4" />
          </Button>
          <div className="hidden items-center gap-2 rounded-full bg-muted px-2 py-1.5 sm:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-[11px] font-semibold text-white">
              {(user?.full_name || "OP").slice(0, 2).toUpperCase()}
            </div>
            <span className="pr-2 text-sm font-medium">{user?.full_name?.split(" ")[0] ?? "Operator"}</span>
          </div>
        </div>
        {open ? (
          <div className="mb-4 grid gap-1 rounded-[1.5rem] bg-white p-2 shadow-card lg:hidden">
            {navItems.map((item) => {
              const isActive = activePath === item.href || (item.href !== "/" && (activePath ?? "").startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn("flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium text-muted-foreground", isActive && "bg-primary text-white")}
                  onClick={() => setOpen(false)}
                >
                  <Icon className="h-4 w-4" />
                  {item.title}
                </Link>
              );
            })}
          </div>
        ) : null}
        {children}
      </main>
    </div>
  );
}
