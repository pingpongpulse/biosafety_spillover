import React, { useState, useEffect } from 'react';
import { Shield, Activity, Beaker, Map as MapIcon, ChevronRight, Server } from 'lucide-react';
import BioRiskEvaluator from './components/BioRiskEvaluator';
import DiscordanceMap from './components/DiscordanceMap';

function App() {
  const [activeTab, setActiveTab] = useState('evaluator');
  const [result, setResult] = useState(null);
  const [explanation, setExplanation] = useState(null);

  return (
    <div className="min-h-screen font-sans">
      {/* Header */}
      <header className="bg-white border-b border-stone-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-lime-800" />
            <div>
              <h1 className="text-xl font-bold font-serif text-stone-800 tracking-tight">BioRiskNet</h1>
              <p className="text-xs text-stone-500 font-medium tracking-wide">META-THESIS V3 • ACADEMIC RESEARCH PLATFORM</p>
            </div>
          </div>
          <nav className="flex space-x-1">
            <button 
              onClick={() => setActiveTab('evaluator')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'evaluator' ? 'bg-stone-100 text-stone-900' : 'text-stone-600 hover:bg-stone-50 hover:text-stone-900'}`}
            >
              <div className="flex items-center gap-2">
                <Beaker className="w-4 h-4" /> Evaluator
              </div>
            </button>
            <button 
              onClick={() => setActiveTab('discordance')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'discordance' ? 'bg-stone-100 text-stone-900' : 'text-stone-600 hover:bg-stone-50 hover:text-stone-900'}`}
            >
              <div className="flex items-center gap-2">
                <MapIcon className="w-4 h-4" /> Discordance Map
              </div>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className={activeTab === 'evaluator' ? 'block' : 'hidden'}>
          <BioRiskEvaluator 
            result={result} setResult={setResult}
            explanation={explanation} setExplanation={setExplanation}
          />
        </div>
        <div className={activeTab === 'discordance' ? 'block' : 'hidden'}>
          <DiscordanceMap result={result} />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-stone-100 border-t border-stone-200 mt-12 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-stone-500">
          <p>BioRiskNet: Decoupling Intrinsic Viral Hazard from Sociomedical Containment Policy.</p>
          <p className="mt-1">A Machine Learning Architecture for Pandemic Meta-Analysis.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
