function SettingsPage() {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h3 className="mb-0">Settings</h3>
          <p className="text-muted">Configure integrations and notification policies.</p>
        </div>
        <button className="btn btn-primary">Save Changes</button>
      </div>

      <div className="card card-stat p-4">
        <div className="row g-3">
          <div className="col-md-6">
            <label className="form-label">Alert Threshold (days)</label>
            <input className="form-control" type="number" defaultValue="30" />
          </div>
          <div className="col-md-6">
            <label className="form-label">Notification Email</label>
            <input className="form-control" type="email" placeholder="security@example.com" />
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
