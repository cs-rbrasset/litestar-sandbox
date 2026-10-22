import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type Toast = { id: number; text: string; error: boolean };
type Notify = (text: string, error?: boolean) => void;

const ToastContext = createContext<Notify>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const notify = useCallback<Notify>((text, error = false) => {
    const id = Date.now() + Math.random();
    setToasts((current) => [...current, { id, text, error }]);
    setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), error ? 6000 : 3000);
  }, []);

  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div className="pointer-events-none fixed right-4 bottom-4 z-50 flex w-80 flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto rounded-xl px-4 py-3 text-sm whitespace-pre-line shadow-lg ${
              t.error ? "bg-rose-600 text-white" : "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
            }`}
          >
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useNotify = () => useContext(ToastContext);
