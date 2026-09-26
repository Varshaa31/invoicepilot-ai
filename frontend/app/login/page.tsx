"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  api,
  setAccessToken,
  setStoredUser,
} from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError(null);
    setLoading(true);

    try {
      const result = await api.login({
        email,
        password,
      });

      setAccessToken(result.access_token);
      setStoredUser(result.user);

      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to sign in.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-ink text-white">
      <div className="mx-auto min-h-screen max-w-7xl px-5 sm:px-8 lg:px-10">
        {/* Top bar */}
        <header className="flex items-center justify-between py-7">
          <Link
            href="/"
            className="font-serif text-2xl tracking-tight transition hover:text-gold"
          >
            InvoicePilot AI
          </Link>

          <Link
            href="/"
            className="text-sm text-white/50 transition hover:text-white"
          >
            ← Back to home
          </Link>
        </header>

        {/* Main layout */}
        <div className="grid min-h-[calc(100vh-110px)] items-center gap-12 py-10 lg:grid-cols-[1fr_0.9fr] lg:gap-20 lg:py-16">
          {/* Left product panel */}
          <section className="max-w-xl">
            <p className="text-sm font-medium uppercase tracking-[0.25em] text-gold">
              Welcome back
            </p>

            <h1 className="mt-5 max-w-xl font-serif text-5xl leading-[1.05] tracking-tight sm:text-6xl">
              Your invoices, ready to move forward.
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-white/55">
              Sign in to continue creating, reviewing, approving, and
              managing your invoices from one workspace.
            </p>

            {/* Workflow preview */}
            <div className="mt-10 overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.04]">
              <div className="border-b border-white/10 px-6 py-5">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-gold">
                  Invoice workflow
                </p>
              </div>

              <div className="divide-y divide-white/10">
                <div className="flex items-center gap-4 px-6 py-5">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gold text-sm font-semibold text-ink">
                    01
                  </span>

                  <div>
                    <p className="font-medium">
                      Customer message
                    </p>

                    <p className="mt-1 text-sm text-white/40">
                      Start with a natural-language request.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 px-6 py-5">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/10 text-sm font-semibold text-white/70">
                    02
                  </span>

                  <div>
                    <p className="font-medium">
                      Service verification
                    </p>

                    <p className="mt-1 text-sm text-white/40">
                      Match services and verify catalog prices.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 px-6 py-5">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/10 text-sm font-semibold text-white/70">
                    03
                  </span>

                  <div>
                    <p className="font-medium">
                      Review & approval
                    </p>

                    <p className="mt-1 text-sm text-white/40">
                      Review the calculated invoice before export.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <p className="mt-7 text-sm text-white/35">
              AI interprets. Your catalog prices. The application calculates.
              You approve.
            </p>
          </section>

          {/* Login form */}
          <section className="w-full">
            <div className="rounded-[2rem] bg-white p-7 text-ink shadow-2xl sm:p-9 lg:p-10">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-gold">
                  Sign in
                </p>

                <h2 className="mt-3 font-serif text-4xl leading-tight">
                  Welcome back
                </h2>

                <p className="mt-2 text-ink/55">
                  Access your invoice workspace.
                </p>
              </div>

              {error && (
                <div className="mt-6 rounded-2xl bg-rose-50 px-4 py-3 text-sm leading-5 text-rose-800">
                  {error}
                </div>
              )}

              <form
                onSubmit={handleSubmit}
                className="mt-8 space-y-5"
              >
                <div>
                  <label
                    htmlFor="email"
                    className="text-sm font-medium"
                  >
                    Email
                  </label>

                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(event) =>
                      setEmail(event.target.value)
                    }
                    className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3.5 outline-none transition placeholder:text-ink/35 focus:border-gold focus:ring-2 focus:ring-gold/20"
                    placeholder="you@example.com"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="text-sm font-medium"
                  >
                    Password
                  </label>

                  <input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3.5 outline-none transition placeholder:text-ink/35 focus:border-gold focus:ring-2 focus:ring-gold/20"
                    placeholder="Your password"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-full bg-ink px-5 py-3.5 font-medium text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading ? "Signing in..." : "Sign in"}
                </button>
              </form>

              <div className="mt-7 border-t border-ink/10 pt-6 text-center">
                <p className="text-sm text-ink/55">
                  Don't have an account?{" "}
                  <Link
                    href="/signup"
                    className="font-medium text-ink underline underline-offset-4 transition hover:text-gold"
                  >
                    Create one
                  </Link>
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}