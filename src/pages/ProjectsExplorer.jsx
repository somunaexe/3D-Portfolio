import { useEffect, useMemo, useRef, useState } from 'react'
import { PLATFORMS, STACKS } from '../constants/projectMeta.js'
import {
    allProjects,
    DEFAULT_FILTERS,
    filterProjects,
    filtersFromSearch,
    filtersToSearch,
    languageOptions,
    PAGE_SIZES,
    pageList,
    paginate,
    SORTS,
    sortProjects,
} from '../lib/projectSearch.js'

const controlClass =
    'w-full rounded-lg bg-black-300 text-white px-3 py-2 border border-black-500 focus:outline-none focus:ring-2 focus:ring-blue-500'

const formatDate = (date) =>
    date ? new Date(`${date}T00:00:00`).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' }) : null

const Field = ({ label, children }) => (
    <label className="flex flex-col gap-1 text-sm text-white-600">
        {label}
        {children}
    </label>
)

const Select = ({ value, onChange, options, anyLabel }) => (
    <select className={controlClass} value={value} onChange={(e) => onChange(e.target.value)}>
        {anyLabel && <option value="">{anyLabel}</option>}
        {options.map(([optionValue, optionLabel]) => (
            <option key={optionValue} value={optionValue}>
                {optionLabel}
            </option>
        ))}
    </select>
)

const ProjectCard = ({ project }) => {
    const added = formatDate(project.date)
    return (
        <article className="flex flex-col gap-4 rounded-xl bg-black-200 border border-black-300 p-5 hover:border-black-500 transition-colors">
            <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded-full bg-blue-500/20 text-blue-200 px-2.5 py-1">{project.platform}</span>
                <span className="rounded-full bg-white/10 text-white-700 px-2.5 py-1">{project.stack}</span>
                <span className="ml-auto text-white-500">{added ? `Added ${added}` : 'Date unavailable'}</span>
            </div>
            <div>
                <h2 className="text-white text-xl font-semibold">{project.title}</h2>
                <p className="mt-2 text-white-600">{project.desc}</p>
            </div>
            <p className="text-sm text-white-500">{project.languages.join(' · ')}</p>
            <div className="flex flex-wrap gap-2">
                {project.tags
                    .filter((tag) => tag.path)
                    .slice(0, 8)
                    .map((tag) => (
                        <div key={tag.name} className="tech-logo !w-8 !h-8 !p-1.5" title={tag.name}>
                            <img src={tag.path} alt={tag.name} />
                        </div>
                    ))}
            </div>
            <div className="flex flex-wrap gap-4 mt-auto pt-2 text-white-600">
                {project.href && (
                    <a className="flex items-center gap-2 hover:text-white" href={project.href} target="_blank" rel="noreferrer">
                        Live site <img src="/assets/arrow-up.png" alt="" className="w-3 h-3" />
                    </a>
                )}
                <a className="flex items-center gap-2 hover:text-white" href={project.repo} target="_blank" rel="noreferrer">
                    GitHub <img src="/assets/arrow-up.png" alt="" className="w-3 h-3" />
                </a>
            </div>
        </article>
    )
}

const Pagination = ({ page, totalPages, onChange }) => {
    if (totalPages <= 1) return null
    const stepClass = 'min-w-10 h-10 px-3 rounded-lg border border-black-500 bg-black-300 text-white disabled:opacity-40 disabled:cursor-not-allowed'
    return (
        <nav aria-label="Pagination" className="flex flex-wrap items-center justify-center gap-2 mt-10">
            <button className={stepClass} onClick={() => onChange(page - 1)} disabled={page === 1}>
                Previous
            </button>
            {pageList(page, totalPages).map((item, index) =>
                item === '…' ? (
                    <span key={`gap-${index}`} className="px-1 text-white-500">…</span>
                ) : (
                    <button
                        key={item}
                        onClick={() => onChange(item)}
                        aria-current={item === page ? 'page' : undefined}
                        className={`${stepClass} ${item === page ? '!bg-blue-600 !border-blue-600' : ''}`}
                    >
                        {item}
                    </button>
                ),
            )}
            <button className={stepClass} onClick={() => onChange(page + 1)} disabled={page === totalPages}>
                Next
            </button>
        </nav>
    )
}

const ProjectsExplorer = () => {
    const [filters, setFilters] = useState(() => filtersFromSearch(window.location.search))
    const resultsRef = useRef(null)

    // Any change to a filter sends you back to page 1; only a page change keeps its page.
    const update = (patch) => setFilters((prev) => ({ ...prev, page: 1, ...patch }))

    const toggleLanguage = (language) =>
        update({
            languages: filters.languages.includes(language)
                ? filters.languages.filter((l) => l !== language)
                : [...filters.languages, language],
        })

    const results = useMemo(
        () => paginate(sortProjects(filterProjects(allProjects, filters), filters.sort), filters.page, filters.pageSize),
        [filters],
    )

    // Keep the address bar in sync so a filtered view can be shared or refreshed.
    useEffect(() => {
        const search = filtersToSearch({ ...filters, page: results.page })
        window.history.replaceState(null, '', `${window.location.pathname}${search}`)
    }, [filters, results.page])

    const goToPage = (page) => {
        update({ page })
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }

    const isFiltered = Boolean(filters.q || filters.platform || filters.stack || filters.languages.length > 0 || filters.live)

    // Sort order and page size are view preferences, so "clear" leaves them alone.
    const clearFilters = () =>
        update({ q: DEFAULT_FILTERS.q, platform: '', stack: '', languages: [], live: false })

    return (
        <div className="min-h-screen text-white-600">
            <header className="border-b border-black-300 bg-black/90">
                <div className="max-w-7xl mx-auto c-space py-5 flex items-center justify-between gap-4">
                    <a href="/#projects" className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors">
                        <img src="/assets/left-arrow.png" alt="" className="w-4 h-4" />
                        Back to portfolio
                    </a>
                    <span className="font-bold text-xl text-neutral-400">SuperSomu</span>
                </div>
            </header>

            <main className="max-w-7xl mx-auto c-space py-10">
                <h1 className="head-text">All Projects</h1>
                <p className="mt-3 max-w-2xl">Search, filter and sort everything I&apos;ve built.</p>

                <section aria-label="Filters" className="mt-8 rounded-xl bg-black-200 border border-black-300 p-5 flex flex-col gap-5">
                    <Field label="Search">
                        <input
                            type="search"
                            className={controlClass}
                            placeholder="Title, technology, description…"
                            value={filters.q}
                            onChange={(e) => update({ q: e.target.value })}
                        />
                    </Field>

                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        <Field label="Platform">
                            <Select value={filters.platform} onChange={(platform) => update({ platform })} anyLabel="Any platform" options={PLATFORMS.map((p) => [p, p])} />
                        </Field>
                        <Field label="Stack">
                            <Select value={filters.stack} onChange={(stack) => update({ stack })} anyLabel="Any stack" options={STACKS.map((s) => [s, s])} />
                        </Field>
                        <Field label="Sort by">
                            <Select value={filters.sort} onChange={(sort) => update({ sort })} options={Object.entries(SORTS)} />
                        </Field>
                        <Field label="Per page">
                            <Select value={String(filters.pageSize)} onChange={(size) => update({ pageSize: Number(size) })} options={PAGE_SIZES.map((n) => [String(n), String(n)])} />
                        </Field>
                    </div>

                    <div>
                        <p className="text-sm mb-2">Languages (any of)</p>
                        <div className="flex flex-wrap gap-2">
                            {languageOptions.map((language) => {
                                const active = filters.languages.includes(language)
                                return (
                                    <button
                                        key={language}
                                        aria-pressed={active}
                                        onClick={() => toggleLanguage(language)}
                                        className={`rounded-full px-3 py-1 text-sm border transition-colors ${active ? 'bg-blue-600 border-blue-600 text-white' : 'bg-black-300 border-black-500 text-white-600 hover:text-white'}`}
                                    >
                                        {language}
                                    </button>
                                )
                            })}
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={filters.live} onChange={(e) => update({ live: e.target.checked })} className="w-4 h-4" />
                            Has a live site
                        </label>
                        {isFiltered && (
                            <button className="text-sm underline hover:text-white" onClick={clearFilters}>
                                Clear filters
                            </button>
                        )}
                    </div>
                </section>

                <p ref={resultsRef} className="mt-8 mb-4 scroll-mt-6" aria-live="polite">
                    {results.total === 0
                        ? 'No projects match.'
                        : `Showing ${results.from}–${results.to} of ${results.total} project${results.total === 1 ? '' : 's'}`}
                </p>

                {results.total === 0 ? (
                    <div className="rounded-xl border border-dashed border-black-500 p-10 text-center">
                        <p className="text-white text-lg">Nothing found</p>
                        <p className="mt-1">Try fewer words or clear a filter.</p>
                    </div>
                ) : (
                    <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                        {results.items.map((project) => (
                            <ProjectCard key={project.id} project={project} />
                        ))}
                    </div>
                )}

                <Pagination page={results.page} totalPages={results.totalPages} onChange={goToPage} />
            </main>
        </div>
    )
}

export default ProjectsExplorer
