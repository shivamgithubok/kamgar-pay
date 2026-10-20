"use client";

import Link from "next/link";
import { LogOut } from "lucide-react";

import { useAuth } from "@/contexts/auth-context";
import { navItems } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

type AppSidebarProps = {
  activePath?: string;
};

export function AppSidebar({ activePath = "/" }: AppSidebarProps) {
  const { user, signOut } = useAuth();
  const initials = (user?.full_name || "Operator")
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <aside className="sticky top-4 hidden h-[calc(100vh-2rem)] w-[248px] shrink-0 rounded-[1.7rem] bg-white/90 p-4 shadow-card lg:flex lg:flex-col">
      <div className="mb-7 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-sm font-bold text-white">L</div>
        <div>
          <p className="text-sm font-semibold text-labour-ink">Labour ERP</p>
          <p className="text-xs text-muted-foreground">Operations</p>
        </div>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const isActive = activePath === item.href || (item.href !== "/" && activePath.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                isActive && "bg-primary text-white shadow-glow hover:bg-primary hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.title}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex items-center gap-3 rounded-2xl bg-muted p-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-xs font-semibold text-white">{initials}</div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{user?.full_name ?? "Operator"}</p>
          <p className="truncate text-xs text-muted-foreground">{user?.email ?? "Signed in"}</p>
        </div>
        <button className="rounded-full p-2 text-muted-foreground hover:bg-white" onClick={signOut} type="button" aria-label="Sign out">
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </aside>
  );
}
