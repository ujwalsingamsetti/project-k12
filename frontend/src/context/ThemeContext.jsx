import { createContext, useContext, useState, useEffect } from 'react';

const ThemeCtx = createContext(null);
export const useTheme = () => useContext(ThemeCtx);

export function ThemeProvider({ children }) {
    const [dark, setDark] = useState(() => {
        const stored = localStorage.getItem('theme');
        if (stored) return stored === 'dark';
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    });

    useEffect(() => {
        const root = document.documentElement;
        if (dark) {
            root.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            root.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [dark]);

    const toggle = () => setDark(d => !d);

    return (
        <ThemeCtx.Provider value={{ dark, toggle }}>
            {children}
        </ThemeCtx.Provider>
    );
}
