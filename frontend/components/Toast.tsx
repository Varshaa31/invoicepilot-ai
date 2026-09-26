"use client";

import { createContext, ReactNode, useContext, useMemo, useState } from "react";

type Toast = { id: number; message: string; tone: "ok" | "err" };

const ToastContext = createContext<{ push: (message: string, tone?: "ok" | "err") => void }>({
  push: () => undefined,
});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const api = useMemo(
    () => ({
      push(message: string, tone: "ok" | "err" = "ok") {
        const id = Date.now();
        setItems((current) => [...current, { id, message, tone }]);
        setTimeout(() => setItems((current) => current.filter((item) => item.id !== id)), 4200);
      },
    }),
    [],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 space-y-2">
        {items.map((item) => (
          <div
            key={item.id}
            className={`pointer-events-auto rounded-xl px-4 py-3 text-sm shadow-lg ${
              item.tone === "ok" ? "bg-ink text-white" : "bg-rose-700 text-white"
            }`}
          >
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
