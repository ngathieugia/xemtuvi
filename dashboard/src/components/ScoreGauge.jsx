const R = 80
const ARC = Math.PI * R

function zone(score) {
  if (score >= 70) return { cls: 'up', txt: 'Thuận lợi' }
  if (score >= 55) return { cls: 'warn', txt: 'Khá' }
  if (score >= 40) return { cls: 'flat', txt: 'Trung tính' }
  return { cls: 'down', txt: 'Bất lợi' }
}

export default function ScoreGauge({ score, verdict, why }) {
  const z = zone(score)
  const off = ARC * (1 - score / 100)
  return (
    <div className="card score-card">
      <span className="label">Điểm cơ hội mua</span>
      <div className="gauge">
        <svg viewBox="0 0 200 112" role="img" aria-label={`Điểm ${score} trên 100`}>
          <path d={`M20 100 A${R} ${R} 0 0 1 180 100`} className="g-track" />
          <path d={`M20 100 A${R} ${R} 0 0 1 180 100`} className={`g-val ${z.cls}`}
                strokeDasharray={ARC} strokeDashoffset={off} />
        </svg>
        <div className="g-num"><b>{score}</b><span>/100</span></div>
      </div>
      <div className={`verdict ${z.cls}`}>{verdict.replace(/^\S+\s/, '')}</div>
      <ul className="why">
        {why.map((w, i) => {
          const [pts, ...rest] = w.split(' ')
          const n = Number(pts)
          return (
            <li key={i}>
              <span className={`pts ${n > 0 ? 'up' : 'down'}`}>{pts}</span>
              <span>{rest.join(' ')}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
