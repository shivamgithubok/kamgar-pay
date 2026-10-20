import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold", {
  variants: {
    variant: {
      default: "bg-slate-900 text-white",
      success: "bg-emerald-50 text-emerald-600",
      warning: "bg-amber-50 text-amber-600",
      muted: "bg-slate-100 text-slate-500",
      clay: "bg-indigo-50 text-indigo-600",
      danger: "bg-rose-50 text-rose-600",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
