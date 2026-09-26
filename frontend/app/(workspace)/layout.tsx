import { AppShell } from "@/components/AppShell";
import { AuthGuard } from "@/components/AuthGuard";
import { ReactNode } from "react";

export default function WorkspaceLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  );
}