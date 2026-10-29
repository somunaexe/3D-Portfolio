import { useSyncExternalStore } from 'react'
import { DEFAULT_THEME, THEME_STORAGE_KEY, THEMES } from '../constants/themes.js'

// The inline script in index.html / projects.html has already put the saved theme
// on <html data-theme> before React loads (no flash of the wrong theme), so the
// attribute is the single source of truth and this store just reads it back.

const root = document.documentElement
const listeners = new Set()
const isTheme = (id) => THEMES.some((theme) => theme.id === id)

const getTheme = () => {
    const current = root.getAttribute('data-theme')
    return isTheme(current) ? current : DEFAULT_THEME
}

const apply = (id) => {
    root.setAttribute('data-theme', id)
    root.setAttribute('data-mode', THEMES.find((theme) => theme.id === id).mode)
}

const notify = () => listeners.forEach((listener) => listener())

export const setTheme = (id) => {
    if (!isTheme(id)) return
    apply(id)
    try {
        localStorage.setItem(THEME_STORAGE_KEY, id)
    } catch {
        // storage blocked (private mode etc.): the theme still applies for this visit
    }
    notify()
}

// Picking a theme in one tab (e.g. the portfolio) updates any other open tab
// (e.g. the project explorer) too.
window.addEventListener('storage', (event) => {
    if (event.key === THEME_STORAGE_KEY && isTheme(event.newValue)) {
        apply(event.newValue)
        notify()
    }
})

const subscribe = (listener) => {
    listeners.add(listener)
    return () => listeners.delete(listener)
}

export const useTheme = () => [useSyncExternalStore(subscribe, getTheme, () => DEFAULT_THEME), setTheme]
