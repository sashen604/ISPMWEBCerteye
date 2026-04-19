function CertificatesPage() {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h3 className="mb-0">Certificates</h3>
          <p className="text-muted">Manage and track all certificates.</p>
        </div>
        <button className="btn btn-outline-primary">Export</button>
      </div>

      <div className="card card-stat p-4">
        <div className="d-flex gap-2 mb-3">
          <input className="form-control" placeholder="Search by thumbprint or subject" />
          <select className="form-select" style={{ maxWidth: '200px' }}>
            <option>All Risk Levels</option>
            <option>Critical</option>
            <option>High</option>
            <option>Normal</option>
            <option>Expired</option>
          </select>
        </div>
        <div className="text-muted">No certificate records loaded.</div>
      </div>
    </div>
  )
}

export default CertificatesPage
