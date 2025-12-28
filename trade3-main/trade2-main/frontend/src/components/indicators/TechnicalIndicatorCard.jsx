import React from 'react';

/**
 * Technical Indicator Card Component
 * Displays technical indicators with colored badges, progress bars, and interpretations
 */

const TechnicalIndicatorCard = ({ icon, title, value, interpretation, type, additionalData }) => {
  // Determine badge color based on interpretation type
  const getBadgeColor = () => {
    switch (type) {
      case 'trend_weak':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'trend_strong':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'oversold':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'overbought':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'neutral':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
      case 'low_volume':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'high_volume':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'medium_volatility':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'high_volatility':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  const getValueColor = () => {
    switch (type) {
      case 'trend_strong':
      case 'oversold':
      case 'high_volume':
        return 'text-green-400';
      case 'overbought':
      case 'high_volatility':
        return 'text-red-400';
      case 'low_volume':
      case 'medium_volatility':
        return 'text-orange-400';
      default:
        return 'text-blue-400';
    }
  };

  // Calculate progress bar percentage for certain indicators
  const getProgressPercentage = () => {
    if (title.includes('ADX')) {
      return Math.min((value / 60) * 100, 100); // ADX max ~60
    }
    if (title.includes('RSI')) {
      return value; // RSI is already 0-100
    }
    return 50; // Default
  };

  const progressPercentage = getProgressPercentage();

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all">
      {/* Header with Icon and Title */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{icon}</span>
          <div>
            <h4 className="text-sm font-semibold text-gray-200">{title}</h4>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full font-bold text-lg ${getValueColor()}`}>
          {value.toFixed(2)}
        </div>
      </div>

      {/* Progress Bar (for ADX and RSI) */}
      {(title.includes('ADX') || title.includes('RSI')) && (
        <div className="mb-3">
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Interpretation Badge */}
      <div className={`inline-flex items-center px-3 py-1.5 rounded-md border font-medium text-sm mb-2 ${getBadgeColor()}`}>
        {interpretation}
      </div>

      {/* Additional Data */}
      {additionalData && (
        <div className="text-xs text-gray-400 mt-2">
          {additionalData}
        </div>
      )}
    </div>
  );
};

// EMA Component (different layout)
export const EMAIndicatorCard = ({ emas }) => {
  return (
    <div className="bg-gray-900/50 backdrop-blur-sm rounded-lg p-4 border border-white/10 hover:border-white/20 transition-all">
      <h4 className="text-sm font-semibold text-gray-200 mb-3">EMAs</h4>
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(emas).map(([key, value]) => (
          <div key={key} className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">{key}:</span>
            <span className="text-gray-200 font-mono text-sm font-semibold">{value?.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TechnicalIndicatorCard;
