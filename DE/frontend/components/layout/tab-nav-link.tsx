"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

export function TabNavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(href + "/");
  return (
    <Link
      href={href}
      className={clsx(
        "block rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "bg-pd-green-50 text-pd-green-700"
          : "text-pd-ink-700 hover:bg-neutral-100",
      )}
    >
      {children}
    </Link>
  );
}
