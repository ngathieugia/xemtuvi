import { useEffect, useRef, useState } from 'react'
import {
  CandlestickSeries, ColorType, CrosshairMode, HistogramSeries, LineSeries, LineStyle,
  createChart, createSeriesMarkers,
} from 'lightweight-charts'

const C = {
  up: '#2ebd85', down: '#f6465d', text: '#a69fbd', grid: 'rgba(255,255,255,0.05)',
  ut: '#f3b54a', scUp: '#2ebd85', scDn: '#f6465d', scFlat: '#8a84a3',
  e20: '#5aa9ff', e50: '#c084fc', bb: 'rgba(200,190,230,0.35)', rsi: '#c084fc',
}

const OVERLAYS = [
  { k: 'ut', label: 'UT Bot', color: C.ut },
  { k: 'sc', label: 'Step Channel', color: C.scUp },
  { k: 'ema', label: 'EMA 20/50', color: C.e20 },
  { k: 'bb', label: 'Bollinger', color: '#c8bee6' },
  { k: 'vol', label: 'Khối lượng', color: '#6b6385' },
]

function readToggles() {
  try { return { ut: true, sc: true, ema: false, bb: false, vol: true, ...JSON.parse(localStorage.getItem('pi.ov') || '{}') } }
  catch { return { ut: true, sc: true, ema: false, bb: false, vol: true } }
}

const line = (rows, key, colorFn) =>
  rows.map((r) => (r[key] == null ? { time: r.t } : { time: r.t, value: r[key], ...(colorFn ? { color: colorFn(r) } : {}) }))

export default function PriceChart({ data }) {
  const box = useRef(null)
  const api = useRef(null)
  const lastTf = useRef(null)
  const [on, setOn] = useState(readToggles)

  // Tạo biểu đồ một lần
  useEffect(() => {
    const chart = createChart(box.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' }, textColor: C.text,
        fontFamily: "'Be Vietnam Pro', system-ui, sans-serif", fontSize: 11,
        panes: { separatorColor: 'rgba(255,255,255,0.08)' },
      },
      grid: { vertLines: { color: C.grid }, horzLines: { color: C.grid } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: true, rightOffset: 4 },
      localization: {
        timeFormatter: (t) => new Date(t * 1000).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }),
      },
    })
    const fmt = { type: 'price', precision: 4, minMove: 0.0001 }
    const s = {
      candle: chart.addSeries(CandlestickSeries, {
        upColor: C.up, downColor: C.down, wickUpColor: C.up, wickDownColor: C.down, borderVisible: false, priceFormat: fmt,
      }),
      vol: chart.addSeries(HistogramSeries, { priceScaleId: 'vol', priceFormat: { type: 'volume' }, lastValueVisible: false, priceLineVisible: false }),
      ut: chart.addSeries(LineSeries, { lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: fmt }),
      scu: chart.addSeries(LineSeries, { lineWidth: 1, lineStyle: LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: fmt }),
      scl: chart.addSeries(LineSeries, { lineWidth: 1, lineStyle: LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: fmt }),
      e20: chart.addSeries(LineSeries, { color: C.e20, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: fmt }),
      e50: chart.addSeries(LineSeries, { color: C.e50, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: fmt }),
      bbu: chart.addSeries(LineSeries, { color: C.bb, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: fmt }),
      bbl: chart.addSeries(LineSeries, { color: C.bb, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: fmt }),
      rsi: chart.addSeries(LineSeries, { color: C.rsi, lineWidth: 1.5, priceLineVisible: false, priceFormat: { type: 'price', precision: 1, minMove: 0.1 } }, 1),
    }
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
    for (const [v, c] of [[70, C.down], [30, C.up]]) {
      s.rsi.createPriceLine({ price: v, color: c, lineStyle: LineStyle.Dotted, lineWidth: 1, axisLabelVisible: false })
    }
    chart.panes()[1]?.setHeight(90)
    const markers = createSeriesMarkers(s.candle, [])
    api.current = { chart, s, markers, lines: [] }
    return () => { chart.remove(); api.current = null }
  }, [])

  // Đổ dữ liệu
  useEffect(() => {
    const a = api.current
    if (!a || !data) return
    const rows = data.candles
    const { s } = a
    s.candle.setData(rows.map((r) => ({ time: r.t, open: r.o, high: r.h, low: r.l, close: r.c })))
    s.vol.setData(rows.map((r) => ({ time: r.t, value: r.v, color: r.c >= r.o ? 'rgba(46,189,133,0.35)' : 'rgba(246,70,93,0.35)' })))
    s.ut.setData(line(rows, 'ut', (r) => (r.c > r.ut ? C.up : C.down)))
    const scColor = (r) => (r.sct === 1 ? C.scUp : r.sct === -1 ? C.scDn : C.scFlat)
    s.scu.setData(line(rows, 'scu', scColor))
    s.scl.setData(line(rows, 'scl', scColor))
    s.e20.setData(line(rows, 'e20'))
    s.e50.setData(line(rows, 'e50'))
    s.bbu.setData(line(rows, 'bbu'))
    s.bbl.setData(line(rows, 'bbl'))
    s.rsi.setData(line(rows, 'rsi'))
    a.markers.setMarkers(rows.filter((r) => r.sig).map((r) => (r.sig === 'BUY'
      ? { time: r.t, position: 'belowBar', color: C.up, shape: 'arrowUp', text: 'Mua' }
      : { time: r.t, position: 'aboveBar', color: C.down, shape: 'arrowDown', text: 'Bán' })))
    a.lines.forEach((l) => s.candle.removePriceLine(l))
    a.lines = [
      ...(data.levels || []).map((p) => s.candle.createPriceLine({ price: p, color: '#f3b54a', lineStyle: LineStyle.Dashed, lineWidth: 1, title: `Mốc ${p}` })),
      ...data.sr.supports.slice(0, 1).map((p) => s.candle.createPriceLine({ price: p, color: 'rgba(46,189,133,0.6)', lineStyle: LineStyle.Dotted, lineWidth: 1, title: 'Hỗ trợ' })),
      ...data.sr.resistances.slice(0, 1).map((p) => s.candle.createPriceLine({ price: p, color: 'rgba(246,70,93,0.6)', lineStyle: LineStyle.Dotted, lineWidth: 1, title: 'Kháng cự' })),
    ]
    if (lastTf.current !== data.tf) {
      const bars = (box.current?.clientWidth ?? 800) < 600 ? 60 : 120
      a.chart.timeScale().setVisibleLogicalRange({ from: rows.length - bars, to: rows.length + 4 })
      lastTf.current = data.tf
    }
  }, [data])

  // Bật/tắt lớp chỉ báo
  useEffect(() => {
    const a = api.current
    if (!a) return
    const { s } = a
    s.ut.applyOptions({ visible: on.ut })
    s.scu.applyOptions({ visible: on.sc })
    s.scl.applyOptions({ visible: on.sc })
    s.e20.applyOptions({ visible: on.ema })
    s.e50.applyOptions({ visible: on.ema })
    s.bbu.applyOptions({ visible: on.bb })
    s.bbl.applyOptions({ visible: on.bb })
    s.vol.applyOptions({ visible: on.vol })
    try { localStorage.setItem('pi.ov', JSON.stringify(on)) } catch { /* bỏ qua */ }
  }, [on])

  return (
    <section className="card chart-card">
      <div className="chart-head">
        <span className="label">Biểu đồ {data?.tf} · khung dưới: RSI 14</span>
        <div className="toggles">
          {OVERLAYS.map((o) => (
            <button key={o.k} className={on[o.k] ? 'on' : ''} onClick={() => setOn((p) => ({ ...p, [o.k]: !p[o.k] }))}>
              <i style={{ background: o.color }} />{o.label}
            </button>
          ))}
        </div>
      </div>
      <div className="chart" ref={box} />
    </section>
  )
}
