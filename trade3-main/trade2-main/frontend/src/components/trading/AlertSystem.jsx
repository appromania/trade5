import { useState, useEffect, useCallback, useRef } from 'react';
import { Bell, BellOff, X, AlertTriangle, Target, Trash2, Volume2, VolumeX } from 'lucide-react';

// Alert storage key
const ALERTS_STORAGE_KEY = 'trading_alerts';

// Alert sound - using Web Audio API for a clean notification sound
const playAlertSound = () => {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // Create oscillator for the notification sound
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Set up a pleasant notification sound
    oscillator.frequency.setValueAtTime(880, audioContext.currentTime); // A5
    oscillator.frequency.setValueAtTime(1100, audioContext.currentTime + 0.1); // C#6
    oscillator.frequency.setValueAtTime(1320, audioContext.currentTime + 0.2); // E6
    
    oscillator.type = 'sine';
    
    // Volume envelope
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.05);
    gainNode.gain.linearRampToValueAtTime(0.2, audioContext.currentTime + 0.15);
    gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.4);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.4);
  } catch (error) {
    console.log('Audio not supported:', error);
  }
};

export default function AlertSystem({ analysis, isOpen, onClose }) {
  const [alerts, setAlerts] = useState([]);
  const [notificationPermission, setNotificationPermission] = useState('default');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const lastCheckRef = useRef({});

  // Load alerts and settings from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(ALERTS_STORAGE_KEY);
    if (stored) {
      setAlerts(JSON.parse(stored));
    }
    
    const soundSetting = localStorage.getItem('alert_sound_enabled');
    if (soundSetting !== null) {
      setSoundEnabled(JSON.parse(soundSetting));
    }
    
    // Check notification permission
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
  }, []);

  // Save alerts to localStorage
  useEffect(() => {
    localStorage.setItem(ALERTS_STORAGE_KEY, JSON.stringify(alerts));
  }, [alerts]);

  // Save sound setting
  useEffect(() => {
    localStorage.setItem('alert_sound_enabled', JSON.stringify(soundEnabled));
  }, [soundEnabled]);

  // Request notification permission
  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
    }
  };

  // Calculate optimal buy zone for R/R = 2.0
  const calculateOptimalZone = useCallback(() => {
    if (!analysis?.risk_management) return null;

    const currentPrice = parseFloat(analysis.current_price);
    const sl = parseFloat(analysis.risk_management.stop_loss);
    const tp = parseFloat(analysis.risk_management.take_profit);
    const targetRR = 2.0;

    // optimalEntry = (TP + targetRR * SL) / (targetRR + 1)
    const optimalEntry = (tp + targetRR * sl) / (targetRR + 1);
    
    return {
      symbol: analysis.symbol,
      currentPrice,
      optimalEntry: optimalEntry.toFixed(2),
      sl: sl.toFixed(2),
      tp: tp.toFixed(2),
      priceToOptimal: ((currentPrice - optimalEntry) / currentPrice * 100).toFixed(2)
    };
  }, [analysis]);

  // Add new alert
  const addAlert = () => {
    const zone = calculateOptimalZone();
    if (!zone) return;

    const newAlert = {
      id: Date.now(),
      symbol: zone.symbol,
      targetPrice: parseFloat(zone.optimalEntry),
      currentPrice: zone.currentPrice,
      sl: zone.sl,
      tp: zone.tp,
      type: 'pullback',
      status: 'active',
      createdAt: new Date().toISOString(),
      triggered: false,
      seen: false
    };

    setAlerts(prev => [...prev, newAlert]);
    setIsMonitoring(true);
  };

  // Remove alert
  const removeAlert = (id) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  // Clear all alerts
  const clearAlerts = () => {
    setAlerts([]);
    setIsMonitoring(false);
  };

  // Test sound
  const testSound = () => {
    playAlertSound();
  };

  // Check alerts against current price
  useEffect(() => {
    if (!analysis || !isMonitoring) return;

    const currentPrice = parseFloat(analysis.current_price);
    
    alerts.forEach(alert => {
      if (alert.symbol === analysis.symbol && 
          alert.status === 'active' && 
          !alert.triggered) {
        
        // Prevent duplicate triggers
        const lastCheck = lastCheckRef.current[alert.id];
        if (lastCheck && Date.now() - lastCheck < 60000) return;
        
        // Check if price reached target
        if (currentPrice <= alert.targetPrice) {
          lastCheckRef.current[alert.id] = Date.now();
          
          // Play alert sound
          if (soundEnabled) {
            playAlertSound();
          }
          
          // Trigger notification
          if (notificationPermission === 'granted') {
            new Notification(`🎯 ALERTĂ ACTIVĂ: ${alert.symbol}`, {
              body: `Prețul ($${currentPrice.toFixed(2)}) a atins zona optimă de BUY!\nR/R > 2.0 | Entry: $${alert.targetPrice.toFixed(2)}`,
              icon: '/favicon.ico',
              tag: `alert-${alert.id}`,
              requireInteraction: true
            });
          }

          // Update alert status
          setAlerts(prev => prev.map(a => 
            a.id === alert.id 
              ? { ...a, triggered: true, status: 'triggered', triggeredAt: new Date().toISOString() }
              : a
          ));
        }
      }
    });
  }, [analysis, alerts, isMonitoring, notificationPermission, soundEnabled]);

  const optimalZone = calculateOptimalZone();
  const activeAlerts = alerts.filter(a => a.status === 'active');
  const triggeredAlerts = alerts.filter(a => a.status === 'triggered');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Alert Panel - Popup style */}
      <div className="relative w-full max-w-sm bg-[#0a0a0a] border border-[#262626] rounded-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-[#121212] border-b border-[#262626] p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`h-8 w-8 rounded flex items-center justify-center ${isMonitoring ? 'bg-yellow-500/20' : 'bg-white/5'}`}>
              {isMonitoring ? (
                <Bell className="h-4 w-4 text-yellow-400 icon-pulse" />
              ) : (
                <BellOff className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
            <div>
              <h2 className="font-bold text-sm uppercase tracking-wider">Alerte Smart Entry</h2>
              <p className="text-[10px] text-muted-foreground">
                {activeAlerts.length} active • {triggeredAlerts.length} declanșate
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-4 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Sound Toggle */}
          <div className="flex items-center justify-between p-3 glass-card rounded">
            <div className="flex items-center gap-2">
              {soundEnabled ? (
                <Volume2 className="h-4 w-4 text-primary" />
              ) : (
                <VolumeX className="h-4 w-4 text-muted-foreground" />
              )}
              <span className="text-sm">Alertă Sonoră</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={testSound}
                className="text-[10px] text-muted-foreground hover:text-primary px-2 py-1 rounded border border-white/10"
              >
                Test
              </button>
              <button
                onClick={() => setSoundEnabled(!soundEnabled)}
                className={`w-10 h-5 rounded-full transition-colors ${soundEnabled ? 'bg-primary' : 'bg-white/10'}`}
              >
                <div className={`w-4 h-4 bg-white rounded-full transition-transform ${soundEnabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
            </div>
          </div>

          {/* Notification Permission */}
          {notificationPermission !== 'granted' && (
            <button
              onClick={requestNotificationPermission}
              className="w-full p-3 bg-yellow-500/10 border border-yellow-500/30 rounded text-sm text-yellow-400 flex items-center justify-center gap-2 hover:bg-yellow-500/20 transition-colors"
            >
              <Bell className="h-4 w-4" />
              Activează Notificările Browser
            </button>
          )}

          {/* Current Symbol Zone */}
          {optimalZone && (
            <div className="glass-card p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="indicator-label flex items-center gap-2">
                  <Target className="h-3 w-3" />
                  {optimalZone.symbol} - Zona Optimă
                </h3>
                <span className={`text-xs px-2 py-1 rounded ${
                  parseFloat(optimalZone.priceToOptimal) <= 2 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-white/5 text-muted-foreground'
                }`}>
                  {parseFloat(optimalZone.priceToOptimal) <= 0 ? 'ÎN ZONĂ!' : `${optimalZone.priceToOptimal}% distanță`}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                <div>
                  <span className="text-xs text-muted-foreground">Preț Curent</span>
                  <p className="font-mono font-bold">${parseFloat(optimalZone.currentPrice).toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">Entry Optim (R/R=2.0)</span>
                  <p className="font-mono font-bold text-primary">${optimalZone.optimalEntry}</p>
                </div>
              </div>

              <button
                onClick={addAlert}
                disabled={alerts.some(a => a.symbol === optimalZone.symbol && a.status === 'active')}
                className="w-full console-btn flex items-center justify-center gap-2"
              >
                <Bell className="h-4 w-4" />
                {alerts.some(a => a.symbol === optimalZone.symbol && a.status === 'active') 
                  ? 'Alertă Activă'
                  : '🔔 Monitorizează Pullback'
                }
              </button>
            </div>
          )}

          {/* Active Alerts */}
          {activeAlerts.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="indicator-label">Alerte Active</h3>
                <button
                  onClick={clearAlerts}
                  className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1"
                >
                  <Trash2 className="h-3 w-3" />
                  Șterge toate
                </button>
              </div>
              <div className="space-y-2">
                {activeAlerts.map(alert => (
                  <div key={alert.id} className="glass-card p-3 flex items-center justify-between">
                    <div>
                      <p className="font-mono text-sm font-bold">{alert.symbol}</p>
                      <p className="text-xs text-muted-foreground">
                        Target: ${alert.targetPrice.toFixed(2)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
                      <button
                        onClick={() => removeAlert(alert.id)}
                        className="p-1 hover:bg-white/10 rounded"
                      >
                        <X className="h-3 w-3 text-muted-foreground" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Triggered Alerts */}
          {triggeredAlerts.length > 0 && (
            <div>
              <h3 className="indicator-label mb-2">Alerte Declanșate</h3>
              <div className="space-y-2">
                {triggeredAlerts.map(alert => (
                  <div key={alert.id} className="bg-green-500/10 border border-green-500/30 p-3 rounded flex items-center justify-between">
                    <div>
                      <p className="font-mono text-sm font-bold text-green-400">{alert.symbol}</p>
                      <p className="text-xs text-green-400/70">
                        ✓ Declanșată la ${alert.targetPrice.toFixed(2)}
                      </p>
                    </div>
                    <button
                      onClick={() => removeAlert(alert.id)}
                      className="p-1 hover:bg-white/10 rounded"
                    >
                      <X className="h-3 w-3 text-muted-foreground" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {alerts.length === 0 && optimalZone && (
            <div className="text-center py-6 text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Nicio alertă activă</p>
              <p className="text-xs mt-1">Adaugă o alertă pentru a fi notificat când prețul atinge zona optimă</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-[#262626] p-3 text-[10px] text-muted-foreground/50 text-center">
          {soundEnabled ? '🔊' : '🔇'} Alertele funcționează doar când aplicația este deschisă
        </div>
      </div>
    </div>
  );
}

// Alert Indicator Component (for header)
export function AlertIndicator({ alerts, onClick }) {
  const activeCount = alerts?.filter(a => a.status === 'active').length || 0;
  const hasTriggered = alerts?.some(a => a.status === 'triggered' && !a.seen);

  return (
    <button
      onClick={onClick}
      className={`relative p-2 rounded transition-colors ${
        hasTriggered 
          ? 'bg-green-500/20 text-green-400' 
          : activeCount > 0 
            ? 'bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20' 
            : 'hover:bg-white/5 text-muted-foreground'
      }`}
    >
      <Bell className={`h-5 w-5 ${activeCount > 0 ? 'icon-pulse' : ''}`} />
      {activeCount > 0 && (
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500 text-black text-[10px] font-bold rounded-full flex items-center justify-center">
          {activeCount}
        </span>
      )}
      {hasTriggered && (
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-ping"></span>
      )}
    </button>
  );
}
