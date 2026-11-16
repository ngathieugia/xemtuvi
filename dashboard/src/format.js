export const fp = (v, d = 4) => (v == null || Number.isNaN(v) ? '–' : Number(v).toFixed(d))
export const pct = (v) => (v == null ? '–' : `${v > 0 ? '+' : ''}${v.toFixed(2)}%`)
export const tone = (v) => (v > 0 ? 'up' : v < 0 ? 'down' : 'flat')
export const timeVN = (sec) =>
  new Date(sec * 1000).toLocaleString('vi-VN', {
    hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', timeZone: 'Asia/Ho_Chi_Minh',
  })
export const trendLabel = (t) => (t === 1 ? 'TĂNG' : t === -1 ? 'GIẢM' : 'ĐI NGANG')
export const trendTone = (t) => (t === 1 ? 'up' : t === -1 ? 'down' : 'flat')
