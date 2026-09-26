"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { clearAccessToken, getStoredUser } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/create", label: "Create Invoice" },
  { href: "/invoices", label: "Invoices" },
  { href: "/services", label: "Service Catalog" },
  { href: "/settings", label: "Settings" },
];

type StoredUser = {
  name?: string;
  email?: string;
};

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  function closeMenu() {
    setOpen(false);
  }

  function handleLogout() {
    clearAccessToken();
    router.replace("/login");
  }

  const displayName = user?.name || "Workspace user";
  const displayEmail = user?.email || "";

  return (
    <div className="min-h-screen bg-[#f4efe6] text-ink">
      <div className="flex min-h-screen">
        {/* Mobile overlay */}
        {open && (
          <button
            type="button"
            aria-label="Close navigation"
            className="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm lg:hidden"
            onClick={closeMenu}
          />
        )}

        {/* Sidebar */}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-[min(84vw,18rem)] flex-col bg-ink p-5 text-white shadow-2xl transition-transform duration-200 lg:static lg:z-auto lg:w-72 lg:translate-x-0 lg:shadow-none ${
            open ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          {/* Brand */}
          <div className="flex items-start justify-between gap-4">
            <Link href="/" className="min-w-0" onClick={closeMenu}>
              <p className="font-serif text-2xl tracking-tight">
                InvoicePilot AI
              </p>
              <p className="mt-2 max-w-xs text-sm leading-5 text-white/55">
                Turn customer messages into professional invoices.
              </p>
            </Link>

            <button
              type="button"
              aria-label="Close navigation"
              className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white lg:hidden"
              onClick={closeMenu}
            >
              <span className="text-xl leading-none">×</span>
            </button>
          </div>

          {/* Navigation */}
          <nav className="mt-8 space-y-1.5" aria-label="Main navigation">
            {NAV.map((item) => {
              const active =
                pathname === item.href ||
                pathname.startsWith(`${item.href}/`);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={closeMenu}
                  className={`flex min-h-11 items-center rounded-xl px-4 py-3 text-sm font-medium transition ${
                    active
                      ? "bg-gold text-ink shadow-sm"
                      : "text-white/75 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="mt-auto border-t border-white/10 pt-5">
            <div className="rounded-2xl bg-white/5 p-4">
              <p className="truncate text-sm font-medium text-white">
                {displayName}
              </p>

              {displayEmail && (
                <p className="mt-1 truncate text-xs text-white/45">
                  {displayEmail}
                </p>
              )}

              <button
                type="button"
                onClick={handleLogout}
                className="mt-4 w-full rounded-xl border border-white/10 px-3 py-2.5 text-left text-sm text-white/70 transition hover:bg-white/10 hover:text-white"
              >
                Log out
              </button>
            </div>

            <div className="mt-5 hidden lg:block">
              <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-gold">
                InvoicePilot
              </p>
              <p className="mt-2 text-sm leading-6 text-white/55">
                Create, review, approve, and manage invoices in one workspace.
              </p>
            </div>
          </div>
        </aside>

        {/* Main area */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Header */}
          <header className="sticky top-0 z-30 flex min-h-16 items-center justify-between gap-3 border-b border-ink/10 bg-white/85 px-4 backdrop-blur-md sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              {/* Mobile menu button */}
              <button
                type="button"
                aria-label="Open navigation"
                aria-expanded={open}
                className="inline-flex h-10 items-center justify-center rounded-xl border border-ink/10 bg-white px-3 text-sm font-medium transition hover:bg-ivory lg:hidden"
                onClick={() => setOpen(true)}
              >
                <span className="mr-2 text-base">☰</span>
                Menu
              </button>

              {/* Desktop workspace label */}
              <div className="hidden min-w-0 lg:block">
                <p className="truncate text-sm font-medium text-ink/80">
                  Workspace
                </p>
                <p className="truncate text-xs text-ink/45">
                  Manage your invoices and services
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Desktop user name */}
              <div className="hidden text-right sm:block">
                <p className="max-w-40 truncate text-sm font-medium text-ink/80">
                  {displayName}
                </p>
                {displayEmail && (
                  <p className="max-w-40 truncate text-xs text-ink/45">
                    {displayEmail}
                  </p>
                )}
              </div>

              <Link
                href="/create"
                className="inline-flex min-h-10 shrink-0 items-center justify-center rounded-full bg-ink px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-ink/90 sm:px-5"
              >
                <span className="mr-1.5 text-base leading-none">+</span>
                <span className="hidden xs:inline">Create Invoice</span>
                <span className="xs:hidden">Create</span>
              </Link>
            </div>
          </header>

          {/* Page content */}
          <main className="w-full flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-8 lg:py-10">
            <div className="mx-auto w-full max-w-7xl">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}