import React, { useState } from 'react';
import { AlertCircle, RefreshCw, Trash2, Check } from 'lucide-react';

/**
 * CertificateActionsCell
 *
 * Provides three actions for certificates:
 * - Acknowledge: Sets acknowledged_at (only for internal_agent source_type)
 * - Rescan: Recalculates risk, days_remaining, status, last_scanned, last_verified
 * - Delete: Removes certificate with confirmation (admin only)
 *
 * Props:
 *   certificate: The certificate object with { id, source_type, ... }
 *   isAdmin: Boolean indicating if user is admin
 *   onAcknowledge: (cert) => Promise - callback after successful acknowledge
 *   onRescan: (cert) => Promise - callback after successful rescan
 *   onDelete: (certId) => Promise - callback after successful delete
 *   onError: (message) => void - callback for error messages
 *   onSuccess: (message) => void - callback for success messages (clears after 5s)
 */
export default function CertificateActionsCell({
  certificate,
  isAdmin,
  onAcknowledge,
  onRescan,
  onDelete,
  onError,
  onSuccess,
}) {
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isInternalAgent = certificate?.source_type === 'internal_agent';

  const handleAcknowledge = async () => {
    setLoading(true);
    try {
      await onAcknowledge(certificate);
      onSuccess(`Certificate ${certificate.domain} acknowledged.`);
    } catch (error) {
      onError(error.message || 'Failed to acknowledge certificate');
    } finally {
      setLoading(false);
    }
  };

  const handleRescan = async () => {
    setLoading(true);
    try {
      await onRescan(certificate);
      onSuccess(`Certificate ${certificate.domain} rescanned.`);
    } catch (error) {
      onError(error.message || 'Failed to rescan certificate');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setLoading(true);
    try {
      await onDelete(certificate.id);
      onSuccess(`Certificate ${certificate.domain} deleted.`);
      setShowDeleteConfirm(false);
    } catch (error) {
      onError(error.message || 'Failed to delete certificate');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Acknowledge - only for internal_agent */}
      {isInternalAgent && (
        <button
          onClick={handleAcknowledge}
          disabled={loading}
          className={`p-2 rounded transition ${
            loading
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
          }`}
          title="Mark as reviewed"
        >
          <Check size={18} />
        </button>
      )}

      {/* Rescan */}
      <button
        onClick={handleRescan}
        disabled={loading || !isAdmin}
        className={`p-2 rounded transition ${
          loading || !isAdmin
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-amber-100 text-amber-600 hover:bg-amber-200'
        }`}
        title={isAdmin ? 'Recalculate risk & expiry' : 'Admin only'}
      >
        <RefreshCw size={18} />
      </button>

      {/* Delete */}
      <button
        onClick={() => setShowDeleteConfirm(true)}
        disabled={loading || !isAdmin}
        className={`p-2 rounded transition ${
          loading || !isAdmin
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-red-100 text-red-600 hover:bg-red-200'
        }`}
        title={isAdmin ? 'Delete certificate' : 'Admin only'}
      >
        <Trash2 size={18} />
      </button>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-sm">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="text-red-600" size={24} />
              <h3 className="text-lg font-semibold">Delete Certificate?</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete <span className="font-mono font-bold">{certificate.domain}</span>?
              This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={loading}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={loading}
                className={`px-4 py-2 bg-red-600 text-white rounded transition ${
                  loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-red-700'
                }`}
              >
                {loading ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
