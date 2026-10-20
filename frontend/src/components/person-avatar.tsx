import { cn } from "@/lib/utils";

const palette = ["bg-indigo-100 text-indigo-700", "bg-sky-100 text-sky-700", "bg-violet-100 text-violet-700", "bg-emerald-100 text-emerald-700", "bg-amber-100 text-amber-700"];

type PersonAvatarProps = {
  name: string;
  className?: string;
};

export function PersonAvatar({ name, className }: PersonAvatarProps) {
  const initials = name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  const tone = palette[name.length % palette.length];

  return (
    <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold", tone, className)}>
      {initials || "W"}
    </div>
  );
}
