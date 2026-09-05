import React from 'react';
import { Icons } from './constants';

export const ThemeToggle = ({ theme, setTheme }) => {
    return (
        <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            className="p-2 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:scale-110 transition-transform focus:outline-none"
            aria-label="Toggle theme"
        >
            {theme === 'light' ? <Icons.Moon className="w-5 h-5" /> : <Icons.Sun className="w-5 h-5" />}
        </button>
    );
};
