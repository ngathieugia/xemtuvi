export default function BuyPlan({ plan }) {
  if (!plan?.length) return null
  return (
    <div className="card">
      <span className="label">Kế hoạch mua tham khảo (DCA)</span>
      <ol className="plan">
        {plan.map((p, i) => <li key={i}>{p}</li>)}
      </ol>
    </div>
  )
}
