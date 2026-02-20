import { createContext, useContext, useState, useCallback } from 'react';
import { MdCheckCircle, MdError, MdInfo, MdWarning, MdClose } from 'react-icons/md';

/* ── Context ─────────────────────────────────────────────────────────────────── */
const ToastCtx = createContext(null);

export const useToast = () => useContext(ToastCtx);

const ICONS = {
    success: <MdCheckCircle className="w-5 h-5 shrink-0" />,
    error: <MdError className="w-5 h-5 shrink-0" />,
    info: <MdInfo className="w-5 h-5 shrink-0" />,
    warning: <MdWarning className="w-5 h-5 shrink-0" />,
};

const STYLES = {
    success: 'bg-white dark:bg-slate-800 border-emerald-100 dark:border-emerald-900/50 text-emerald-600 dark:text-emerald-400',
    error: 'bg-white dark:bg-slate-800 border-red-100 dark:border-red-900/50 text-red-600 dark:text-red-400',
    info: 'bg-white dark:bg-slate-800 border-blue-100 dark:border-blue-900/50 text-blue-600 dark:text-blue-400',
    warning: 'bg-white dark:bg-slate-800 border-amber-100 dark:border-amber-900/50 text-amber-600 dark:text-amber-400',
};

/* ── Single Toast Item ───────────────────────────────────────────────────────── */
function ToastItem({ toast, onDismiss }) {
    return (
        <div
            className={`toast-enter flex items-center gap-3.5 px-6 py-4 rounded-[1.25rem] border shadow-[0_10px_40px_-15px_rgba(0,0,0,0.1)] dark:shadow-none text-sm font-bold max-w-sm transition-all duration-500 scale-100 opacity-100 ${STYLES[toast.type]}`}
            role="alert"
        >
            <div className="flex-shrink-0">
                {ICONS[toast.type]}
            </div>
            <span className="flex-1 text-slate-700 dark:text-slate-100 font-bold">{toast.message}</span>
            <button onClick={() => onDismiss(toast.id)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors ml-2 opacity-40 hover:opacity-100">
                <MdClose size={18} />
            </button>
        </div>
    );
}

/* ── Provider ────────────────────────────────────────────────────────────────── */
export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);

    const dismiss = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const show = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => dismiss(id), duration);
        return id;
    }, [dismiss]);

    const toast = {
        success: (msg, dur) => show(msg, 'success', dur),
        error: (msg, dur) => show(msg, 'error', dur),
        info: (msg, dur) => show(msg, 'info', dur),
        warning: (msg, dur) => show(msg, 'warning', dur),
    };

    return (
        <ToastCtx.Provider value={toast}>
            {children}
            {/* Toast container */}
            <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3">
                {toasts.map(t => (
                    <ToastItem key={t.id} toast={t} onDismiss={dismiss} />
                ))}
            </div>
        </ToastCtx.Provider>
    );
}
