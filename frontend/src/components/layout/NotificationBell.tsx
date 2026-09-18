import React, { useState, useEffect, useRef } from 'react';
import { Bell, Check, Zap, Info, AlertTriangle, Sun, Settings } from 'lucide-react';
import { cn } from '../../utils/cn';

type NotificationType = 'success' | 'info' | 'warning';

interface AppNotification {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: NotificationType;
}

const DUMMY_NOTIFICATIONS: AppNotification[] = [
  {
    id: "1",
    title: "Optimization completed",
    message: "Your 24-hour energy plan is ready.",
    time: "2 min ago",
    read: false,
    type: "success"
  },
  {
    id: "2",
    title: "Directive interpreted",
    message: "Battery reserve instruction was successfully interpreted.",
    time: "8 min ago",
    read: false,
    type: "info"
  },
  {
    id: "3",
    title: "Battery warning",
    message: "Battery level is approaching the minimum reserve.",
    time: "15 min ago",
    read: false,
    type: "warning"
  },
  {
    id: "4",
    title: "Solar availability",
    message: "High solar availability detected in the current plan.",
    time: "1 hour ago",
    read: true,
    type: "success"
  },
  {
    id: "5",
    title: "Constraint warning",
    message: "An operator constraint may affect schedule feasibility.",
    time: "2 hours ago",
    read: true,
    type: "warning"
  }
];

export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>(DUMMY_NOTIFICATIONS);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  const handleMarkAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const handleMarkAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'success':
        return <Zap className="h-4 w-4 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'info':
      default:
        return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
        aria-label="Notifications"
      >
        <div className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white ring-2 ring-white">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </div>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 origin-top-right rounded-xl bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50 overflow-hidden flex flex-col max-h-[85vh] sm:max-h-[600px] animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 bg-slate-50/50">
            <h3 className="text-sm font-semibold text-slate-900">Notifications</h3>
            {unreadCount > 0 && (
              <button 
                onClick={handleMarkAllAsRead}
                className="text-xs font-medium text-green-600 hover:text-green-700 hover:underline transition-all"
              >
                Mark all as read
              </button>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {notifications.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {notifications.map((notification) => (
                  <div 
                    key={notification.id} 
                    onClick={() => handleMarkAsRead(notification.id)}
                    className={cn(
                      "flex items-start p-4 hover:bg-slate-50 transition-colors cursor-pointer relative",
                      !notification.read ? "bg-green-50/40" : ""
                    )}
                  >
                    {!notification.read && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-green-500 rounded-r-md"></div>
                    )}
                    <div className={cn(
                      "mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border",
                      notification.type === 'success' ? "bg-green-100 border-green-200" :
                      notification.type === 'warning' ? "bg-amber-100 border-amber-200" :
                      "bg-blue-100 border-blue-200"
                    )}>
                      {getIcon(notification.type)}
                    </div>
                    <div className="ml-3 flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className={cn(
                          "text-sm font-medium",
                          !notification.read ? "text-slate-900" : "text-slate-700"
                        )}>
                          {notification.title}
                        </p>
                        <p className="text-xs text-slate-400 whitespace-nowrap ml-2">
                          {notification.time}
                        </p>
                      </div>
                      <p className="text-sm text-slate-500 line-clamp-2">
                        {notification.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                  <Bell className="h-6 w-6 text-slate-400" />
                </div>
                <p className="text-sm font-medium text-slate-900">No notifications</p>
                <p className="text-sm text-slate-500 mt-1">You're all caught up!</p>
              </div>
            )}
          </div>
          
          <div className="border-t border-slate-100 p-2 bg-slate-50/50">
            <button 
              className="flex w-full items-center justify-center rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <Settings className="mr-2 h-4 w-4" />
              Notification Settings
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
