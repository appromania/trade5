import { HelpCircle, X } from 'lucide-react';
import { useState } from 'react';
import { getIndicatorHelp } from '@/lib/indicatorHelp';

export default function IndicatorTooltip({ indicator }) {
  const [showModal, setShowModal] = useState(false);
  const help = getIndicatorHelp(indicator);

  if (!help) return null;

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="ml-1 text-muted-foreground hover:text-primary transition-colors"
        aria-label="Informații indicator"
      >
        <HelpCircle className="h-3 w-3" />
      </button>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setShowModal(false)}>
          <div className="terminal-card p-6 max-w-lg w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-heading text-xl font-bold">{help.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{help.description}</p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-bold uppercase tracking-wider text-primary mb-2">Interpretare</h4>
                <div className="space-y-2">
                  {Object.entries(help.interpretation).map(([key, value]) => (
                    <div key={key} className="flex items-start gap-2 text-sm">
                      <span className="text-primary mt-1">•</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-primary/10 border border-primary/30 rounded-sm">
                <h4 className="text-sm font-bold uppercase tracking-wider text-primary mb-2">Acțiune</h4>
                <p className="text-sm">{help.action}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
