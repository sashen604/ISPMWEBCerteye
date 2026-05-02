import { useState, useCallback } from 'react';

/**
 * useNotification
 *
 * Hook for managing success/error toast notifications that auto-clear after 5 seconds.
 *
 * Returns: { notifications, addSuccess, addError, removeNotification }
 *
 * Usage:
 *   const { notifications, addSuccess, addError } = useNotification();
 *
 *   addSuccess('Operation completed');
 *   addError('Something went wrong');
 *
 *   // In JSX, render notifications map
 */
export function useNotification() {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((message, type = 'success') => {
    const id = Date.now();
    setNotifications((prev) => [...prev, { id, message, type }]);

    // Auto-clear after 5 seconds
    setTimeout(() => {
      removeNotification(id);
    }, 5000);

    return id;
  }, []);

  const addSuccess = useCallback(
    (message) => addNotification(message, 'success'),
    [addNotification]
  );

  const addError = useCallback(
    (message) => addNotification(message, 'error'),
    [addNotification]
  );

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  return {
    notifications,
    addSuccess,
    addError,
    removeNotification,
  };
}

/**
 * NotificationContainer
 *
 * Displays all active notifications as toasts.
 *
 * Props:
 *   notifications: Array of { id, message, type } from useNotification hook
 *   onRemove: (id) => void - callback to remove notification
 */
export function NotificationContainer({ notifications, onRemove }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {notifications.map((notif) => (
        <div
          key={notif.id}
          className={`px-4 py-3 rounded shadow-lg text-white transition-all animate-slideInUp ${
            notif.type === 'success' ? 'bg-green-600' : 'bg-red-600'
          }`}
        >
          <div className="flex items-center justify-between gap-3">
            <span>{notif.message}</span>
            <button
              onClick={() => onRemove(notif.id)}
              className="text-white hover:opacity-70 transition"
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
