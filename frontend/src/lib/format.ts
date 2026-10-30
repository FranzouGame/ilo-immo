export const scoreColor = (s: number | undefined): string =>
  s == null ? '#888' : s >= 75 ? '#1b9e5a' : s >= 55 ? '#c98a00' : s >= 35 ? '#e06b00' : '#c0392b'

/** Phrase courte résumant pourquoi une annonce a ce score (points forts / faibles). */
export function scoreSummary(b: { label: string; score: number | null }[]): string {
  const known = b.filter((x) => x.score != null) as { label: string; score: number }[]
  const best = known.filter((x) => x.score >= 0.8).slice(0, 2).map((x) => x.label.replace(/ \(.*\)/, ''))
  const worst = known.filter((x) => x.score <= 0.3).slice(0, 2).map((x) => x.label.replace(/ \(.*\)/, ''))
  return [best.length ? `+ ${best.join(', ')}` : '', worst.length ? `- ${worst.join(', ')}` : ''].filter(Boolean).join('  ')
}
