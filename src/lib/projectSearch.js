import { myProjects } from '../constants/index.js'
import { projectMeta } from '../constants/projectMeta.js'

export const allProjects = myProjects.map((project) => ({ ...project, ...projectMeta[project.id] }))

export const languageOptions = [...new Set(allProjects.flatMap((p) => p.languages ?? []))].sort((a, b) => a.localeCompare(b))

export const SORTS = {
    newest: 'Newest added',
    oldest: 'Oldest added',
    az: 'A to Z',
    za: 'Z to A',
}

export const PAGE_SIZES = [6, 9, 12]

export const DEFAULT_FILTERS = {
    q: '',
    platform: '',
    stack: '',
    languages: [],
    live: false,
    sort: 'newest',
    pageSize: 9,
    page: 1,
}

const searchableText = (project) =>
    [
        project.title,
        project.desc,
        project.subdesc,
        project.platform,
        project.stack,
        ...(project.languages ?? []),
        ...project.tags.map((tag) => tag.name),
        ...project.entry,
    ]
        .join(' ')
        .toLowerCase()

// Every word typed must appear somewhere in the project (AND), so
// "react stripe" narrows the results instead of widening them.
export const filterProjects = (projects, { q, platform, stack, languages, live }) => {
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean)
    return projects.filter((project) => {
        if (platform && project.platform !== platform) return false
        if (stack && project.stack !== stack) return false
        if (live && !project.href) return false
        // Several languages = OR: show a project that uses any of them.
        if (languages.length > 0 && !languages.some((lang) => project.languages?.includes(lang))) return false
        if (terms.length > 0) {
            const text = searchableText(project)
            return terms.every((term) => text.includes(term))
        }
        return true
    })
}

const byTitle = (a, b) => a.title.localeCompare(b.title, undefined, { sensitivity: 'base' })

// Projects without a date always sort last, in either direction.
const byDate = (direction) => (a, b) => {
    if (!a.date && !b.date) return byTitle(a, b)
    if (!a.date) return 1
    if (!b.date) return -1
    return direction * a.date.localeCompare(b.date) || byTitle(a, b)
}

export const sortProjects = (projects, sort) => {
    const compare = {
        newest: byDate(-1),
        oldest: byDate(1),
        az: byTitle,
        za: (a, b) => byTitle(b, a),
    }[sort] ?? byTitle
    return [...projects].sort(compare)
}

export const paginate = (items, page, pageSize) => {
    const total = items.length
    const totalPages = Math.max(1, Math.ceil(total / pageSize))
    const current = Math.min(Math.max(1, page), totalPages)
    const start = (current - 1) * pageSize
    return {
        items: items.slice(start, start + pageSize),
        page: current,
        totalPages,
        total,
        from: total === 0 ? 0 : start + 1,
        to: Math.min(start + pageSize, total),
    }
}

// [1, '…', 4, 5, 6, '…', 12]: always first, last and the neighbours of the current page.
export const pageList = (page, totalPages) => {
    const wanted = new Set([1, totalPages, page - 1, page, page + 1])
    const pages = [...wanted].filter((p) => p >= 1 && p <= totalPages).sort((a, b) => a - b)
    return pages.flatMap((p, i) => (i > 0 && p - pages[i - 1] > 1 ? ['…', p] : [p]))
}

// Filters <-> URL query string, so a filtered view can be shared or refreshed.
export const filtersFromSearch = (search) => {
    const params = new URLSearchParams(search)
    const pick = (value, allowed, fallback) => (allowed.includes(value) ? value : fallback)
    const pageSize = Number(params.get('size'))
    return {
        q: params.get('q') ?? DEFAULT_FILTERS.q,
        platform: params.get('platform') ?? '',
        stack: params.get('stack') ?? '',
        languages: params.getAll('lang').filter((lang) => languageOptions.includes(lang)),
        live: params.get('live') === '1',
        sort: pick(params.get('sort'), Object.keys(SORTS), DEFAULT_FILTERS.sort),
        pageSize: PAGE_SIZES.includes(pageSize) ? pageSize : DEFAULT_FILTERS.pageSize,
        page: Math.max(1, parseInt(params.get('page'), 10) || 1),
    }
}

export const filtersToSearch = (f) => {
    const params = new URLSearchParams()
    if (f.q) params.set('q', f.q)
    if (f.platform) params.set('platform', f.platform)
    if (f.stack) params.set('stack', f.stack)
    f.languages.forEach((lang) => params.append('lang', lang))
    if (f.live) params.set('live', '1')
    if (f.sort !== DEFAULT_FILTERS.sort) params.set('sort', f.sort)
    if (f.pageSize !== DEFAULT_FILTERS.pageSize) params.set('size', String(f.pageSize))
    if (f.page > 1) params.set('page', String(f.page))
    const search = params.toString()
    return search ? `?${search}` : ''
}
