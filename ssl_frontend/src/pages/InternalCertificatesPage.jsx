function InternalCertificatesPage() {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h3 className="mb-0">Internal Certificates</h3>
          <p className="text-muted">Monitor certificates issued by internal PKI.</p>
        </div>
        <button className="btn btn-outline-primary">Sync</button>
      </div>

      <div className="card card-stat p-4">
        <div className="text-muted">No internal certificates found.</div>
      </div>
    </div>
  )
}

export default InternalCertificatesPage
