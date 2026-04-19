function AlertsPage() {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h3 className="mb-0">Alerts</h3>
          <p className="text-muted">Review certificates requiring immediate action.</p>
        </div>
        <button className="btn btn-outline-danger">Acknowledge All</button>
      </div>

      <div className="card card-stat p-4">
        <div className="text-muted">No alerts to display.</div>
      </div>
    </div>
  )
}

export default AlertsPage
