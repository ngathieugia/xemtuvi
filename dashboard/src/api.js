// Tự tìm đường dẫn API: trang ở .../pi/app/ -> API ở .../pi/api/data
// (hoạt động cả khi app Python nằm trong thư mục con như /tuvi/pi/app/)
export function apiUrl() {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  const p = window.location.pathname
  const i = p.indexOf('/pi/app')
  const base = i >= 0 ? p.slice(0, i) : ''
  return `${base}/pi/api/data`
}

export async function fetchData(tf, demo) {
  const q = new URLSearchParams({ tf })
  if (demo) q.set('demo', '1')
  const r = await fetch(`${apiUrl()}?${q}`, { cache: 'no-store' })
  const j = await r.json().catch(() => ({}))
  if (!r.ok || j.error) throw new Error(j.error || `Lỗi máy chủ (${r.status})`)
  return j
}
