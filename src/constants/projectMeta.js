// Extra searchable fields for each entry in `myProjects`, keyed by project id.
//
// platform  - where the project runs
// stack     - the kind of engineering work (mirrors the CV's role groupings)
// languages - primary languages used
// date      - "date added": first commit on GitHub (YYYY-MM-DD). It is when the
//             project reached GitHub, which can be later than when it was built.
//             null = no public repo yet, these sort last.

export const PLATFORMS = ['Web', 'Mobile', 'Desktop & VR', 'Cloud & Server', 'Command line', 'Data science']

export const STACKS = ['Full-Stack', 'Frontend', 'Backend', 'AI / ML', 'Cloud & DevOps', 'Mobile', 'Game Dev', 'Tools & Scripts']

export const projectMeta = {
  1:  { platform: 'Web',            stack: 'Full-Stack',      languages: ['C#'],                  date: '2024-09-28' },
  2:  { platform: 'Web',            stack: 'Full-Stack',      languages: ['PHP', 'JavaScript'],   date: '2024-01-21' },
  4:  { platform: 'Desktop & VR',   stack: 'Game Dev',        languages: ['C#'],                  date: '2024-01-21' },
  5:  { platform: 'Mobile',         stack: 'Mobile',          languages: ['Kotlin', 'Swift'],     date: '2024-01-21' },
  6:  { platform: 'Mobile',         stack: 'Mobile',          languages: ['Dart'],                date: '2024-02-23' },
  7:  { platform: 'Web',            stack: 'Frontend',        languages: ['TypeScript'],          date: '2024-09-18' },
  8:  { platform: 'Command line',   stack: 'Tools & Scripts', languages: ['JavaScript'],          date: '2024-09-03' },
  9:  { platform: 'Desktop & VR',   stack: 'Game Dev',        languages: ['Java'],                date: '2024-09-26' },
  10: { platform: 'Command line',   stack: 'Tools & Scripts', languages: ['Python'],              date: '2024-02-17' },
  11: { platform: 'Data science',   stack: 'AI / ML',         languages: ['Python'],              date: '2024-10-26' },
  12: { platform: 'Web',            stack: 'Frontend',        languages: ['JavaScript'],          date: '2024-10-01' },
  13: { platform: 'Command line',   stack: 'Tools & Scripts', languages: ['JavaScript'],          date: '2024-09-29' },
  14: { platform: 'Web',            stack: 'Full-Stack',      languages: ['JavaScript'],          date: '2024-10-15' },
  15: { platform: 'Web',            stack: 'Game Dev',        languages: ['JavaScript'],          date: '2024-01-05' },
  16: { platform: 'Web',            stack: 'Game Dev',        languages: ['JavaScript'],          date: '2024-11-19' },
  17: { platform: 'Cloud & Server', stack: 'Backend',         languages: ['Java'],                date: '2024-11-21' },
  18: { platform: 'Mobile',         stack: 'Mobile',          languages: ['TypeScript'],          date: '2024-11-23' },
  19: { platform: 'Command line',   stack: 'Backend',         languages: ['PHP'],                 date: '2024-12-06' },
  20: { platform: 'Web',            stack: 'Full-Stack',      languages: ['TypeScript', 'Go'],    date: '2026-06-11' },
  21: { platform: 'Cloud & Server', stack: 'AI / ML',         languages: ['Python'],              date: '2026-07-03' },
  22: { platform: 'Data science',   stack: 'AI / ML',         languages: ['Python'],              date: '2026-06-02' },
  23: { platform: 'Data science',   stack: 'AI / ML',         languages: ['Python'],              date: '2026-06-02' },
  24: { platform: 'Data science',   stack: 'AI / ML',         languages: ['Python'],              date: null },
  25: { platform: 'Data science',   stack: 'AI / ML',         languages: ['Python'],              date: '2026-06-02' },
  26: { platform: 'Data science',   stack: 'AI / ML',         languages: ['Python'],              date: '2026-06-02' },
  27: { platform: 'Cloud & Server', stack: 'Cloud & DevOps',  languages: ['JavaScript'],          date: '2026-05-24' },
  28: { platform: 'Mobile',         stack: 'Mobile',          languages: ['Dart'],                date: null },
  29: { platform: 'Desktop & VR',   stack: 'Game Dev',        languages: ['C#'],                  date: '2024-11-13' },
}
