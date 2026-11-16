import { fp, pct } from '../format.js'

export default function Levels({ data }) {
  const { sr, price } = data
  const rows = [
    ...sr.resistances.slice(0, 3).reverse().map((v) => ({ v, k: 'Kháng cự', cls: 'down' })),
    { v: price, k: 'Giá hiện tại', cls: 'now' },
    ...sr.supports.slice(0, 3).map((v) => ({ v, k: 'Hỗ trợ', cls: 'up' })),
  ]
  return (
    <div className="card">
      <span className="label">Hỗ trợ / kháng cự (khung ngày)</span>
      <ul className="ladder">
        {rows.map((r, i) => (
          <li key={i} className={r.cls}>
            <span>{r.k}</span>
            <b className="mono">{fp(r.v)}</b>
            <span className="muted mono">{r.cls === 'now' ? '' : pct((r.v / price - 1) * 100)}</span>
          </li>
        ))}
      </ul>
      <div className="row-kv muted">
        <span>Biên độ 60 ngày</span>
        <span className="mono">{fp(sr.low_range)} – {fp(sr.high_range)}</span>
      </div>
    </div>
  )
}
