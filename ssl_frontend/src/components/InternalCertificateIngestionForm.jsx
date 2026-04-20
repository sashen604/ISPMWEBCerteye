import { useMemo, useState } from 'react'
import api from '../api'

function toIsoString(value) {
  if (!value) return undefined
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return undefined
  return date.toISOString()
}

function InternalCertificateIngestionForm({ onSuccess }) {
  const [mode, setMode] = useState('single')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [rawResponse, setRawResponse] = useState(null)

  const [agentToken, setAgentToken] = useState('')
  const [singleForm, setSingleForm] = useState({
    hostname: '',
    subject: '',
    issuer: '',
    thumbprint: '',
    valid_from: '',
    valid_to: '',
    certificate_template: '',
    signature_algorithm: 'sha256WithRSAEncryption',
    key_length: 2048,
  })

  const [batchJson, setBatchJson] = useState('[\n  {\n    "hostname": "SERVER01",\n    "subject": "CN=server01.example.com",\n    "issuer": "CN=Internal-CA",\n    "thumbprint": "ABC123DEF456",\n    "valid_to": "2027-01-01T00:00:00Z",\n    "certificate_template": "WebServer"\n  }\n]')
  const [updateIfExists, setUpdateIfExists] = useState(true)

  const batchHint = useMemo(() => {
    return 'Paste either a JSON array of certificates or an object with { "certificates": [...] }'
  }, [])

  const handleSingleChange = (event) => {
    const { name, value } = event.target
    setSingleForm((previous) => ({
      ...previous,
      [name]: name === 'key_length' ? Number(value || 0) : value,
    }))
  }

  const resetMessage = () => {
    setMessage({ type: '', text: '' })
    setRawResponse(null)
  }

  const handleSingleSubmit = async (event) => {
    event.preventDefault()
    resetMessage()

    if (!agentToken.trim()) {
      setMessage({ type: 'error', text: 'Agent token is required.' })
      return
    }

    if (!singleForm.hostname || !singleForm.subject || !singleForm.issuer || !singleForm.thumbprint || !singleForm.valid_to) {
      setMessage({ type: 'error', text: 'Please complete all required single-certificate fields.' })
      return
    }

    const payload = {
      agent_token: agentToken.trim(),
      hostname: singleForm.hostname.trim(),
      subject: singleForm.subject.trim(),
      issuer: singleForm.issuer.trim(),
      thumbprint: singleForm.thumbprint.trim(),
      valid_to: toIsoString(singleForm.valid_to) || singleForm.valid_to,
      certificate_template: singleForm.certificate_template.trim() || undefined,
      signature_algorithm: singleForm.signature_algorithm.trim() || 'Unknown',
      key_length: Number(singleForm.key_length) || 2048,
    }

    if (singleForm.valid_from) {
      payload.valid_from = toIsoString(singleForm.valid_from) || singleForm.valid_from
    }

    setLoading(true)
    try {
      const response = await api.post('/api/certificates/collect_internal/', payload)
      setRawResponse(response.data)
      setMessage({
        type: response.data?.success ? 'success' : 'error',
        text: response.data?.message || 'Single certificate request completed.',
      })

      if (response.data?.success && typeof onSuccess === 'function') {
        onSuccess()
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.error || error.response?.data?.message || error.message || 'Single certificate submission failed.',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleBatchSubmit = async (event) => {
    event.preventDefault()
    resetMessage()

    if (!agentToken.trim()) {
      setMessage({ type: 'error', text: 'Agent token is required.' })
      return
    }

    let parsed
    try {
      parsed = JSON.parse(batchJson)
    } catch {
      setMessage({ type: 'error', text: 'Batch JSON is invalid.' })
      return
    }

    let payload
    if (Array.isArray(parsed)) {
      payload = {
        agent_token: agentToken.trim(),
        certificates: parsed,
        update_if_exists: updateIfExists,
      }
    } else if (parsed && Array.isArray(parsed.certificates)) {
      payload = {
        ...parsed,
        agent_token: agentToken.trim(),
        update_if_exists: parsed.update_if_exists ?? updateIfExists,
      }
    } else {
      setMessage({ type: 'error', text: 'Batch JSON must be an array or an object containing "certificates" array.' })
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/api/certificates/collect_internal/', payload)
      setRawResponse(response.data)
      setMessage({
        type: response.data?.success ? 'success' : 'error',
        text: response.data?.message || 'Batch request completed.',
      })

      if (response.data?.created > 0 || response.data?.updated > 0) {
        if (typeof onSuccess === 'function') {
          onSuccess()
        }
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.error || error.response?.data?.message || error.message || 'Batch submission failed.',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.card}>
      <div style={styles.headerRow}>
        <div>
          <h3 style={styles.title}>➕ Add Internal Certificates</h3>
          <p style={styles.subtitle}>Submit directly to `collect_internal` endpoint using an agent token.</p>
        </div>
      </div>

      <div style={styles.inputSection}>
        <label style={styles.label} htmlFor="agent_token">Agent Token *</label>
        <input
          id="agent_token"
          type="text"
          value={agentToken}
          onChange={(event) => setAgentToken(event.target.value)}
          style={styles.input}
          placeholder="Paste agent token"
        />
      </div>

      <div style={styles.tabRow}>
        <button
          type="button"
          style={mode === 'single' ? styles.tabButtonActive : styles.tabButton}
          onClick={() => {
            setMode('single')
            resetMessage()
          }}
        >
          Single Certificate
        </button>
        <button
          type="button"
          style={mode === 'batch' ? styles.tabButtonActive : styles.tabButton}
          onClick={() => {
            setMode('batch')
            resetMessage()
          }}
        >
          Batch JSON Upload
        </button>
      </div>

      {mode === 'single' ? (
        <form onSubmit={handleSingleSubmit} style={styles.formGrid}>
          <div style={styles.field}>
            <label style={styles.label}>Hostname *</label>
            <input name="hostname" value={singleForm.hostname} onChange={handleSingleChange} style={styles.input} placeholder="SERVER01" required />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Subject *</label>
            <input name="subject" value={singleForm.subject} onChange={handleSingleChange} style={styles.input} placeholder="CN=server01.example.com" required />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Issuer *</label>
            <input name="issuer" value={singleForm.issuer} onChange={handleSingleChange} style={styles.input} placeholder="CN=Internal-CA" required />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Thumbprint *</label>
            <input name="thumbprint" value={singleForm.thumbprint} onChange={handleSingleChange} style={styles.input} placeholder="ABC123DEF456" required />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Valid From</label>
            <input name="valid_from" type="datetime-local" value={singleForm.valid_from} onChange={handleSingleChange} style={styles.input} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Valid To *</label>
            <input name="valid_to" type="datetime-local" value={singleForm.valid_to} onChange={handleSingleChange} style={styles.input} required />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Certificate Template</label>
            <input name="certificate_template" value={singleForm.certificate_template} onChange={handleSingleChange} style={styles.input} placeholder="WebServer" />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Signature Algorithm</label>
            <input name="signature_algorithm" value={singleForm.signature_algorithm} onChange={handleSingleChange} style={styles.input} placeholder="sha256WithRSAEncryption" />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Key Length</label>
            <input name="key_length" type="number" min="512" value={singleForm.key_length} onChange={handleSingleChange} style={styles.input} />
          </div>

          <div style={styles.actions}>
            <button type="submit" style={styles.submitButton} disabled={loading}>
              {loading ? 'Submitting...' : 'Submit Single Certificate'}
            </button>
          </div>
        </form>
      ) : (
        <form onSubmit={handleBatchSubmit}>
          <div style={styles.field}>
            <label style={styles.label}>Batch JSON *</label>
            <textarea
              value={batchJson}
              onChange={(event) => setBatchJson(event.target.value)}
              rows={10}
              style={styles.textarea}
            />
            <small style={styles.hint}>{batchHint}</small>
          </div>

          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={updateIfExists}
              onChange={(event) => setUpdateIfExists(event.target.checked)}
            />
            Update existing certificates if thumbprint already exists
          </label>

          <div style={styles.actions}>
            <button type="submit" style={styles.submitButton} disabled={loading}>
              {loading ? 'Submitting...' : 'Submit Batch JSON'}
            </button>
          </div>
        </form>
      )}

      {message.text && (
        <div style={message.type === 'success' ? styles.success : styles.error}>
          {message.text}
        </div>
      )}

      {rawResponse && (
        <details style={styles.details}>
          <summary style={styles.detailsSummary}>Response Details</summary>
          <pre style={styles.pre}>{JSON.stringify(rawResponse, null, 2)}</pre>
        </details>
      )}
    </div>
  )
}

const styles = {
  card: {
    backgroundColor: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    boxShadow: 'var(--shadow)',
    padding: '20px',
  },
  headerRow: {
    marginBottom: '12px',
  },
  title: {
    margin: 0,
    color: 'var(--text)',
    fontSize: '20px',
    fontWeight: 700,
  },
  subtitle: {
    margin: '6px 0 0 0',
    color: 'var(--text-secondary)',
    fontSize: '13px',
  },
  inputSection: {
    marginBottom: '14px',
  },
  tabRow: {
    display: 'flex',
    gap: '10px',
    marginBottom: '14px',
    flexWrap: 'wrap',
  },
  tabButton: {
    border: '1px solid var(--border)',
    backgroundColor: 'var(--surface-2)',
    color: 'var(--text)',
    borderRadius: '10px',
    padding: '8px 12px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  tabButtonActive: {
    border: '1px solid var(--primary)',
    backgroundColor: 'rgba(30, 64, 175, 0.1)',
    color: 'var(--primary)',
    borderRadius: '10px',
    padding: '8px 12px',
    fontWeight: 700,
    cursor: 'pointer',
  },
  formGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '12px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    color: 'var(--text-secondary)',
    fontSize: '12px',
    fontWeight: 700,
    textTransform: 'uppercase',
  },
  input: {
    width: '100%',
    border: '1px solid var(--border)',
    backgroundColor: 'var(--surface-2)',
    color: 'var(--text)',
    borderRadius: '10px',
    padding: '10px 12px',
    fontSize: '13px',
  },
  textarea: {
    width: '100%',
    border: '1px solid var(--border)',
    backgroundColor: 'var(--surface-2)',
    color: 'var(--text)',
    borderRadius: '10px',
    padding: '10px 12px',
    fontSize: '13px',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  },
  hint: {
    color: 'var(--text-secondary)',
    fontSize: '12px',
  },
  checkboxLabel: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    color: 'var(--text)',
    fontSize: '13px',
    marginTop: '8px',
  },
  actions: {
    gridColumn: '1 / -1',
    marginTop: '6px',
  },
  submitButton: {
    border: 'none',
    backgroundColor: 'var(--primary)',
    color: '#ffffff',
    borderRadius: '10px',
    padding: '10px 16px',
    fontWeight: 700,
    cursor: 'pointer',
  },
  success: {
    marginTop: '12px',
    padding: '10px 12px',
    border: '1px solid rgba(22, 163, 74, 0.35)',
    backgroundColor: 'rgba(22, 163, 74, 0.08)',
    color: '#166534',
    borderRadius: '10px',
    fontSize: '13px',
  },
  error: {
    marginTop: '12px',
    padding: '10px 12px',
    border: '1px solid rgba(220, 38, 38, 0.35)',
    backgroundColor: 'rgba(220, 38, 38, 0.08)',
    color: '#b91c1c',
    borderRadius: '10px',
    fontSize: '13px',
  },
  details: {
    marginTop: '12px',
    border: '1px solid var(--border)',
    borderRadius: '10px',
    backgroundColor: 'var(--surface-2)',
    padding: '10px 12px',
  },
  detailsSummary: {
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 700,
    color: 'var(--text)',
  },
  pre: {
    margin: '10px 0 0 0',
    fontSize: '12px',
    color: 'var(--text)',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
}

export default InternalCertificateIngestionForm