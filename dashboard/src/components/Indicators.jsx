import { fp, timeVN, trendLabel, trendTone } from '../format.js'

function Badge({ cls, children }) {
  return <span className={`badge ${cls}`}>{children}</span>
}

function rsiTone(r) {
  if (r == null) return 'flat'
  if (r < 30) return 'up'
  if (r > 70) return 'down'
  return 'flat'
}

export default function Indicators({ data }) {
  const { sig, trend, params, signal_tf: stf, trend_tf: ttf } = data
  const rows = [
    {
      name: `UT Bot Alerts (${params.ut_key}, ${params.ut_atr})`,
      hint: 'Đường trailing stop theo ATR. Giá trên đường = trạng thái MUA.',
      a: <Badge cls={sig.ut_pos === 'LONG' ? 'up' : 'down'}>{sig.ut_pos === 'LONG' ? 'MUA' : 'BÁN'}</Badge>,
      b: <Badge cls={trend.ut_pos === 'LONG' ? 'up' : 'down'}>{trend.ut_pos === 'LONG' ? 'MUA' : 'BÁN'}</Badge>,
      extra: sig.ut_last_signal
        ? `Tín hiệu gần nhất ${stf}: ${sig.ut_last_signal === 'BUY' ? 'MUA' : 'BÁN'} @ ${fp(sig.ut_last_signal_price)} (${timeVN(sig.ut_last_signal_ts / 1000)})`
        : `Stop ${stf}: ${fp(sig.ut_stop)}`,
    },
    {
      name: `Step Channel Momentum (${params.scmt_len}, ${params.scmt_mult})`,
      hint: 'Kênh bậc thang từ pivot ± ATR. Phá kênh trên = xu hướng tăng.',
      a: <Badge cls={trendTone(sig.sc_trend)}>{trendLabel(sig.sc_trend)}</Badge>,
      b: <Badge cls={trendTone(trend.sc_trend)}>{trendLabel(trend.sc_trend)}</Badge>,
      extra: `Kênh ${stf}: ${fp(sig.sc_lo)} – ${fp(sig.sc_up)}`,
    },
    {
      name: 'RSI 14',
      hint: 'Dưới 30 quá bán (giá rẻ), trên 70 quá mua (tránh mua đuổi).',
      a: <Badge cls={rsiTone(sig.rsi)}>{sig.rsi?.toFixed(1) ?? '–'}</Badge>,
      b: <Badge cls={rsiTone(trend.rsi)}>{trend.rsi?.toFixed(1) ?? '–'}</Badge>,
      meter: sig.rsi,
    },
    {
      name: 'MACD (12, 26, 9)',
      hint: 'Histogram dương và tăng dần = động lượng tăng.',
      a: <Badge cls={sig.macd_hist > 0 ? 'up' : 'down'}>{sig.macd_hist > 0 ? 'Dương' : 'Âm'}</Badge>,
      b: <Badge cls={trend.macd_hist > 0 ? 'up' : 'down'}>{trend.macd_hist > 0 ? 'Dương' : 'Âm'}</Badge>,
      extra: `Hist ${stf}: ${sig.macd_hist?.toFixed(6) ?? '–'}`,
    },
    {
      name: 'Bollinger (20, 2)',
      hint: 'Giá chạm dải dưới thường là vùng hồi; vượt dải trên là nóng.',
      a: <Badge cls={bbTone(sig)}>{bbLabel(sig)}</Badge>,
      b: <Badge cls={bbTone(trend)}>{bbLabel(trend)}</Badge>,
      extra: `Dải ${stf}: ${fp(sig.bb_lo)} – ${fp(sig.bb_up)}`,
    },
    {
      name: 'EMA 20 / 50 / 200',
      hint: 'Giá > EMA50 > EMA200 là xu hướng tăng bền.',
      a: <Badge cls={emaTone(sig)}>{emaLabel(sig)}</Badge>,
      b: <Badge cls={emaTone(trend)}>{emaLabel(trend)}</Badge>,
      extra: `${ttf}: ${fp(trend.ema20)} / ${fp(trend.ema50)} / ${fp(trend.ema200)}`,
    },
  ]
  return (
    <div className="card">
      <div className="ind-head">
        <span className="label">Chỉ báo</span>
        <span className="cols"><span>{stf}</span><span>{ttf}</span></span>
      </div>
      <ul className="ind">
        {rows.map((r) => (
          <li key={r.name}>
            <div className="ind-main">
              <div>
                <div className="ind-name">{r.name}</div>
                <div className="muted small">{r.hint}</div>
              </div>
              <span className="cols">{r.a}{r.b}</span>
            </div>
            {r.meter != null && (
              <div className="meter"><i style={{ left: `${r.meter}%` }} /></div>
            )}
            {r.extra && <div className="muted small mono">{r.extra}</div>}
          </li>
        ))}
      </ul>
    </div>
  )
}

const bbTone = (d) => (d.close <= d.bb_lo ? 'up' : d.close >= d.bb_up ? 'down' : 'flat')
const bbLabel = (d) => (d.close <= d.bb_lo ? 'Dải dưới' : d.close >= d.bb_up ? 'Dải trên' : 'Giữa dải')
const emaTone = (d) => (d.close > d.ema50 && d.ema50 > d.ema200 ? 'up' : d.close < d.ema50 && d.ema50 < d.ema200 ? 'down' : 'flat')
const emaLabel = (d) => (emaTone(d) === 'up' ? 'Tăng' : emaTone(d) === 'down' ? 'Giảm' : 'Đan xen')
