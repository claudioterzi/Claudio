// R3∞ — Artifact ritrovato (2026-06-29): «Mon Premier Cirque» come profumo.
// Componente React (stile artifact claude.ai: recharts + shadcn/ui), conservato
// integrale come consegnato da Claudio. Scheda canonica: libro/oggetti/profumo_mon_premier_cirque.md
import React, { useState } from 'react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend } from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const MonPremierCirque = () => {
  const [activeSection, setActiveSection] = useState('all');

  // Dati per il grafico radar delle famiglie olfattive
  const olfattiveData = [
    { subject: 'Floreale', A: 90, B: 80, fullMark: 100 },
    { subject: 'Speziato', A: 75, B: 85, fullMark: 100 },
    { subject: 'Animale', A: 60, B: 70, fullMark: 100 },
    { subject: 'Agrumato', A: 65, B: 55, fullMark: 100 },
    { subject: 'Legnoso', A: 70, B: 75, fullMark: 100 },
    { subject: 'Ambrato', A: 85, B: 90, fullMark: 100 },
  ];

  return (
    <Card className="w-full max-w-4xl bg-gradient-to-br from-amber-50 to-rose-50">
      <CardHeader className="text-center border-b border-amber-200">
        <CardTitle className="text-3xl font-serif text-amber-800">Mon Premier Cirque</CardTitle>
        <p className="text-lg italic text-rose-700 mt-2">
          "Un'estate di scoperte, un piccolo chapiteau nascosto tra i campi..."
        </p>
      </CardHeader>
      <CardContent>
        {/* Sezione Poesia */}
        <div className="my-6 p-6 bg-white/80 rounded-lg shadow-sm">
          <p className="text-gray-700 italic leading-relaxed">
            Un'estate di scoperte, un piccolo chapiteau nascosto tra i campi,
            il suono delle cicale e il calore del tramonto. Un amore impossibile,
            magico, che ha lasciato il ricordo di un desiderio eterno,
            fragile e potente come il primo bacio.
          </p>
        </div>

        {/* Visualizzazione Radar */}
        <div className="h-96 my-8">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart outerRadius={150} data={olfattiveData}>
              <PolarGrid stroke="#d97706" />
              <PolarAngleAxis dataKey="subject" stroke="#92400e" />
              <PolarRadiusAxis stroke="#92400e" />
              <Radar
                name="Intensità"
                dataKey="A"
                stroke="#c2410c"
                fill="#f97316"
                fillOpacity={0.5}
              />
              <Radar
                name="Persistenza"
                dataKey="B"
                stroke="#7c2d12"
                fill="#ea580c"
                fillOpacity={0.3}
              />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Note Olfattive */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-8">
          <div className="p-4 bg-amber-50 rounded-lg">
            <h3 className="text-xl font-serif text-amber-800 mb-4">Note di Testa (30%)</h3>
            <ul className="space-y-2">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>
                <span>Bergamotto: Freschezza serale</span>
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>
                <span>Zafferano: Calore del tramonto</span>
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>
                <span>Fieno: Semplicità campestre</span>
              </li>
            </ul>
          </div>

          <div className="p-4 bg-rose-50 rounded-lg">
            <h3 className="text-xl font-serif text-rose-800 mb-4">Note di Cuore (40%)</h3>
            <ul className="space-y-2">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-rose-500 rounded-full mr-2"></span>
                <span>Tuberosa: Sensualità del primo amore</span>
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-rose-500 rounded-full mr-2"></span>
                <span>Gelsomino: Fiori notturni</span>
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-rose-500 rounded-full mr-2"></span>
                <span>Cannella: Emozione crescente</span>
              </li>
            </ul>
          </div>

          <div className="p-4 bg-orange-50 rounded-lg">
            <h3 className="text-xl font-serif text-orange-800 mb-4">Note di Fondo (30%)</h3>
            <ul className="space-y-2">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                <span>Ambra Grigia: Mistero del desiderio</span>
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                <span>Patchouli: Ancoraggio ai ricordi</span>
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                <span>Castoreum: Passione nascente</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Ingredienti e Kit */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-8">
          <div className="p-4 bg-white/80 rounded-lg">
            <h3 className="text-xl font-serif text-amber-800 mb-4">Ingredienti Disponibili</h3>
            <ul className="space-y-2">
              <li className="text-green-600 flex items-center">
                <span className="text-lg mr-2">✓</span>Bergamotto
              </li>
              <li className="text-green-600 flex items-center">
                <span className="text-lg mr-2">✓</span>Zafferano
              </li>
              <li className="text-green-600 flex items-center">
                <span className="text-lg mr-2">✓</span>Patchouli
              </li>
              <li className="text-green-600 flex items-center">
                <span className="text-lg mr-2">✓</span>Gelsomino
              </li>
              <li className="text-green-600 flex items-center">
                <span className="text-lg mr-2">✓</span>Cannella
              </li>
              <li className="text-green-600 flex items-center">
                <span className="text-lg mr-2">✓</span>Ambra Grigia
              </li>
            </ul>
          </div>

          <div className="p-4 bg-white/80 rounded-lg">
            <h3 className="text-xl font-serif text-amber-800 mb-4">Da Acquisire</h3>
            <ul className="space-y-2">
              <li className="text-red-600 flex items-center">
                <span className="text-lg mr-2">•</span>Fieno (estratto naturale)
              </li>
              <li className="text-red-600 flex items-center">
                <span className="text-lg mr-2">•</span>Castoreum (sintetico)
              </li>
            </ul>
          </div>
        </div>

        {/* Note di Packaging */}
        <div className="p-6 bg-gradient-to-r from-amber-100 to-rose-100 rounded-lg mt-8">
          <h3 className="text-xl font-serif text-amber-800 mb-4">Note sul Packaging</h3>
          <p className="text-gray-700 leading-relaxed">
            Una boccetta dalla forma fluida e luminosa, che cattura l'essenza del
            tendone del circo al tramonto. Il vetro sfumato ricorda i colori caldi
            della sera d'estate, mentre il tappo dorato richiama la magia del momento.
            Un QR code nascosto sotto la base permette di rivivere questa storia
            ogni volta che si desidera.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default MonPremierCirque;
