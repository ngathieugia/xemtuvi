import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchData } from './api.js'
import { fp, pct, tone } from './format.js'
import PriceChart from './components/PriceChart.jsx'
import ScoreGauge from './components/ScoreGauge.jsx'
import Indicators from './components/Indicators.jsx'
import Levels from './components/Levels.jsx'
import BuyPlan from './components/BuyPlan.jsx'

const TFS = ['5m', '15m', '1h', '4h', '1d']
const REFRESH = 30
const DEMO = new URLSearchParams(window.location.search).get('demo') === '1'

function readTf() {
  try { return localStorage.getItem('pi.tf') || '15m' } catch { return '15m' }
}

export default function App() {
  const [tf, setTf] = useState(readTf)
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const [left, setLeft] = useState(REFRESH)
  const prevPrice = useRef(null)
  const [flash, setFlash] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const d = await fetchData(tf, DEMO)
      if (prevPrice.current != null && d.price !== prevPrice.current) {
        setFlash(d.price > prevPrice.current ? 'flash-up' : 'flash-down')
        setTimeout(() => setFlash(''), 900)
      }
      prevPrice.current = d.price
      setData(d)
      setErr('')
      document.title = `${fp(d.price)} · PI Radar`
    } catch (e) {
      setErr(e.message)
    } finally {
      setLoading(false)
      setLeft(REFRESH)
    }
  }, [tf])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    const id = setInterval(() => setLeft((s) => Math.max(0, s - 1)), 1000)
    return () => clearInterval(id)
  }, [])
  useEffect(() => { if (left === 0 && !loading) load() }, [left, loading, load])

  const pickTf = (t) => {
    setTf(t)
    try { localStorage.setItem('pi.tf', t) } catch { /* bỏ qua */ }
  }

  return (
    <div className="page">
      <header className="top">
        <div className="brand">
          <img src="./pi.svg" alt="" width="36" height="36" />
          <div>
            <h1>PI Radar</h1>
            <p className="muted">
              PI/USDT {data?.market === 'spot' ? 'Giao ngay' : 'Perpetual'} · {data?.source ?? '…'}
              {DEMO && <span className="tag">DỮ LIỆU GIẢ LẬP</span>}
            </p>
          </div>
        </div>
        <div className="top-right">
          <div className="seg" role="tablist" aria-label="Khung thời gian">
            {TFS.map((t) => (
              <button key={t} className={t === tf ? 'on' : ''} onClick={() => pickTf(t)}>{t}</button>
            ))}
          </div>
          <button className="refresh" onClick={load} disabled={loading} title="Làm mới">
            <span className={`dot ${err ? 'bad' : 'live'}`} />
            {loading ? 'Đang tải…' : `${left}s`}
          </button>
        </div>
      </header>

      {err && <div className="alert">⚠️ {err}. Sẽ thử lại sau {left}s.</div>}

      {!data ? (
        <div className="skeleton">Đang tải dữ liệu thị trường…</div>
      ) : (
        <>
          <section className="hero">
            <div className="card price-card">
              <span className="label">Giá hiện tại</span>
              <div className={`price ${flash}`}>{fp(data.price)} <small>USDT</small></div>
              <div className="chips">
                {Object.entries(data.chg).map(([k, v]) => (
                  <span key={k} className={`chip ${tone(v)}`}>{k} <b>{pct(v)}</b></span>
                ))}
              </div>
              <RangeBar lo={data.ticker.low24h} hi={data.ticker.high24h} v={data.price} />
              <div className="row-kv">
                <span>Khối lượng 24h</span>
                <b>{Intl.NumberFormat('vi-VN', { notation: 'compact', maximumFractionDigits: 1 }).format(data.ticker.vol24h)}</b>
              </div>
              {data.funding != null && (
                <div className="row-kv">
                  <span>Funding /8h</span>
                  <b className={tone(-data.funding)}>{(data.funding * 100).toFixed(4)}%</b>
                </div>
              )}
            </div>
            <ScoreGauge score={data.score} verdict={data.verdict} why={data.why} />
          </section>

          <PriceChart data={data} />

          <section className="grid2">
            <Indicators data={data} />
            <div className="stack">
              <Levels data={data} />
              <BuyPlan plan={data.plan} />
            </div>
          </section>
        </>
      )}

      <footer className="muted">
        Chỉ mang tính tham khảo kỹ thuật, không phải khuyến nghị đầu tư. Cảnh báo tự động được gửi qua Telegram bởi bot
        chạy trên máy chủ.
      </footer>
    </div>
  )
}

function RangeBar({ lo, hi, v }) {
  const p = hi > lo ? Math.min(100, Math.max(0, ((v - lo) / (hi - lo)) * 100)) : 50
  return (
    <div className="range">
      <div className="range-track"><div className="range-mark" style={{ left: `${p}%` }} /></div>
      <div className="range-lbl"><span>Thấp 24h {fp(lo)}</span><span>Cao 24h {fp(hi)}</span></div>
    </div>
  )
}
