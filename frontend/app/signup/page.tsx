"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  api,
  setAccessToken,
  setStoredUser,
} from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const result = await api.signup({
        name,
        email,
        password,
        confirm_password: confirmPassword,
      });

      setAccessToken(result.access_token);
      setStoredUser(result.user);

      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to create your account.",
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
              Get started
            </p>

            <h1 className="mt-5 max-w-xl font-serif text-5xl leading-[1.05] tracking-tight sm:text-6xl">
              Turn customer messages into professional invoices.
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-white/55">
              Create your InvoicePilot workspace and turn natural-language
              customer requests into structured, price-verified invoices.
            </p>

            {/* Product principles */}
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 text-gold">✓</span>

                  <div>
                    <p className="font-medium text-white">
                      AI-assisted extraction
                    </p>

                    <p className="mt-1 text-sm leading-5 text-white/40">
                      Understand customer requests automatically.
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 text-gold">✓</span>

                  <div>
                    <p className="font-medium text-white">
                      Verified pricing
                    </p>

                    <p className="mt-1 text-sm leading-5 text-white/40">
                      Use your service catalog as the price source.
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 text-gold">✓</span>

                  <div>
                    <p className="font-medium text-white">
                      Automatic calculations
                    </p>

                    <p className="mt-1 text-sm leading-5 text-white/40">
                      Totals are calculated by the application.
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 text-gold">✓</span>

                  <div>
                    <p className="font-medium text-white">
                      Human approval
                    </p>

                    <p className="mt-1 text-sm leading-5 text-white/40">
                      Review the invoice before export.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Workflow */}
            <div className="mt-10 border-t border-white/10 pt-7">
              <p className="text-xs font-medium uppercase tracking-[0.2em] text-white/30">
                Your workflow
              </p>

              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
                <span className="text-white/60">Understand</span>
                <span className="text-gold">→</span>
                <span className="text-white/60">Verify</span>
                <span className="text-gold">→</span>
                <span className="text-white/60">Calculate</span>
                <span className="text-gold">→</span>
                <span className="text-white/60">Review</span>
              </div>
            </div>
          </section>

          {/* Signup form */}
          <section className="w-full">
            <div className="rounded-[2rem] bg-white p-7 text-ink shadow-2xl sm:p-9 lg:p-10">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.2em] text-gold">
                  Create workspace
                </p>

                <h2 className="mt-3 font-serif text-4xl leading-tight">
                  Create your account
                </h2>

                <p className="mt-2 text-ink/55">
                  Set up your invoice workspace.
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
                    htmlFor="name"
                    className="text-sm font-medium"
                  >
                    Full name
                  </label>

                  <input
                    id="name"
                    type="text"
                    autoComplete="name"
                    required
                    value={name}
                    onChange={(event) =>
                      setName(event.target.value)
                    }
                    className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3.5 outline-none transition placeholder:text-ink/35 focus:border-gold focus:ring-2 focus:ring-gold/20"
                    placeholder="Your name"
                  />
                </div>

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
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3.5 outline-none transition placeholder:text-ink/35 focus:border-gold focus:ring-2 focus:ring-gold/20"
                    placeholder="At least 8 characters"
                  />

                  <p className="mt-2 text-xs text-ink/40">
                    Use at least 8 characters.
                  </p>
                </div>

                <div>
                  <label
                    htmlFor="confirmPassword"
                    className="text-sm font-medium"
                  >
                    Confirm password
                  </label>

                  <input
                    id="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={confirmPassword}
                    onChange={(event) =>
                      setConfirmPassword(event.target.value)
                    }
                    className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3.5 outline-none transition placeholder:text-ink/35 focus:border-gold focus:ring-2 focus:ring-gold/20"
                    placeholder="Enter your password again"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-full bg-ink px-5 py-3.5 font-medium text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading
                    ? "Creating account..."
                    : "Create account"}
                </button>
              </form>

              <div className="mt-7 border-t border-ink/10 pt-6 text-center">
                <p className="text-sm text-ink/55">
                  Already have an account?{" "}
                  <Link
                    href="/login"
                    className="font-medium text-ink underline underline-offset-4 transition hover:text-gold"
                  >
                    Sign in
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