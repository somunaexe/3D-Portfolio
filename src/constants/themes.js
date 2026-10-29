// Slider order: light -> dark. The palettes themselves live in index.css as
// :root[data-theme="<id>"] blocks; `mode` drives the icon filter and color-scheme.
//
//   Light / Dark           - the portfolio's own neutral themes (Dark = the original look)
//   Bulfighter Light/Dark  - palettes from the Bulfighter site (orange / pink accents)
//   Bulwriter Light/Dark   - palettes from Bulwriter (cream & bronze / warm brown & gold)

export const THEMES = [
    { id: 'light', label: 'Light', mode: 'light' },
    { id: 'bulfighter-light', label: 'Bulfighter Light', mode: 'light' },
    { id: 'bulwriter-light', label: 'Bulwriter Light', mode: 'light' },
    { id: 'bulwriter-dark', label: 'Bulwriter Dark', mode: 'dark' },
    { id: 'bulfighter-dark', label: 'Bulfighter Dark', mode: 'dark' },
    { id: 'dark', label: 'Dark', mode: 'dark' },
]

export const DEFAULT_THEME = 'dark'
export const THEME_STORAGE_KEY = 'portfolio:theme'
