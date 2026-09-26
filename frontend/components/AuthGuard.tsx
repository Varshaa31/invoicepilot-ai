"use client";

import { ReactNode, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = getAccessToken();

    if (!token) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }

    setChecking(false);
  }, [pathname, router]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f4efe6]">
        <div className="text-center">
          <p className="font-serif text-2xl">InvoicePilot AI</p>
          <p className="mt-2 text-sm text-ink/50">Checking your workspace…</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}