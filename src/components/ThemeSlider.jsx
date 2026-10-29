import { THEMES } from '../constants/themes.js'
import { useTheme } from '../hooks/useTheme.js'

const iconProps = {
    viewBox: '0 0 24 24',
    'aria-hidden': true,
    className: 'w-4 h-4 shrink-0 fill-none stroke-white-600 stroke-2',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
}

const ThemeSlider = ({ className = '' }) => {
    const [theme, setTheme] = useTheme()
    const index = THEMES.findIndex((item) => item.id === theme)
    const { label } = THEMES[index]

    return (
        <div className={`flex items-center gap-2 ${className}`}>
            <svg {...iconProps}>
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
            </svg>
            <input
                type="range"
                min={0}
                max={THEMES.length - 1}
                step={1}
                value={index}
                onChange={(e) => setTheme(THEMES[Number(e.target.value)].id)}
                aria-label="Colour theme"
                aria-valuetext={label}
                title={label}
                className="w-24 cursor-pointer accent-[rgb(var(--theme-accent))]"
            />
            <svg {...iconProps}>
                <path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" />
            </svg>
            <span className="text-xs text-white-600 w-[6.5rem] whitespace-nowrap" aria-hidden="true">
                {label}
            </span>
        </div>
    )
}

export default ThemeSlider
