import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Settings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
      toast.error('Eroare la încărcarea setărilor');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post(`${API}/settings`, settings);
      toast.success('Setări salvate cu succes!');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Eroare la salvarea setărilor');
    } finally {
      setSaving(false);
    }
  };

  const updateProvider = (providerName, field, value) => {
    setSettings((prev) => ({
      ...prev,
      providers: prev.providers.map((p) =>
        p.name === providerName ? { ...p, [field]: value } : p
      ),
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-[#262626] bg-[#0A0A0A]">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button
                variant="outline"
                className="border-white/10 hover:border-primary/50 rounded-sm font-mono uppercase text-xs"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Înapoi
              </Button>
            </Link>
            <div>
              <h1 className="font-heading text-xl font-black uppercase tracking-tight">Setări</h1>
              <p className="text-xs text-muted-foreground uppercase tracking-widest">
                Configurare Provideri de Date
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-6">
          {/* Providers */}
          <div className="terminal-card p-6">
            <h2 className="font-heading text-lg font-bold uppercase tracking-tight mb-6">
              Provideri de Date Financiare
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Configurează providerul de date preferat. Yahoo Finance este gratuit și nu necesită cheie API.
            </p>

            <div className="space-y-6">
              {settings?.providers?.map((provider) => (
                <div key={provider.name} className="border border-white/10 rounded-sm p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="font-mono font-bold uppercase text-sm">
                        {provider.name === 'yahoo' && 'Yahoo Finance'}
                        {provider.name === 'alphavantage' && 'Alpha Vantage'}
                        {provider.name === 'twelvedata' && 'Twelve Data'}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {provider.name === 'yahoo' && 'Gratuit, fără limită'}
                        {provider.name === 'alphavantage' && 'Gratuit: 5 cereri/min, 25/zi'}
                        {provider.name === 'twelvedata' && 'Freemium: 800 cereri/zi'}
                      </div>
                    </div>
                    <Switch
                      checked={provider.enabled}
                      onCheckedChange={(checked) => updateProvider(provider.name, 'enabled', checked)}
                      disabled={provider.name === 'yahoo'}
                    />
                  </div>

                  {provider.name !== 'yahoo' && (
                    <div className="space-y-2">
                      <Label htmlFor={`${provider.name}-key`} className="text-xs uppercase tracking-widest">
                        Cheie API
                      </Label>
                      <Input
                        id={`${provider.name}-key`}
                        type="password"
                        placeholder="Introduceți cheia API..."
                        value={provider.api_key || ''}
                        onChange={(e) => updateProvider(provider.name, 'api_key', e.target.value)}
                        className="bg-black/50 border-white/10 focus:border-primary rounded-sm font-mono"
                      />
                      <p className="text-xs text-muted-foreground">
                        {provider.name === 'alphavantage' && (
                          <>
                            Obțineți o cheie gratuită:{' '}
                            <a
                              href="https://www.alphavantage.co/support/#api-key"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline"
                            >
                              alphavantage.co
                            </a>
                          </>
                        )}
                        {provider.name === 'twelvedata' && (
                          <>
                            Obțineți o cheie gratuită:{' '}
                            <a
                              href="https://twelvedata.com/pricing"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline"
                            >
                              twelvedata.com
                            </a>
                          </>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Info Card */}
          <div className="terminal-card p-6 bg-primary/5 border-primary/20">
            <h3 className="font-mono text-sm font-bold mb-3">💡 Informații Importante</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span>
                  <strong>Yahoo Finance</strong> este recomandat pentru început - este gratuit și nu necesită cheie API.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span>
                  Dacă ajungeți la limita de cereri pe Yahoo, puteți adăuga <strong>Alpha Vantage</strong> sau{' '}
                  <strong>Twelve Data</strong> ca backup.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-1">•</span>
                <span>
                  Cheile API sunt stocate în siguranță și folosite doar pentru a obține date financiare.
                </span>
              </li>
            </ul>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-primary hover:bg-primary/90 text-black font-mono uppercase h-12 px-8 rounded-sm"
            >
              {saving ? (
                <div className="h-5 w-5 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Salvează Setările
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}