import React, { useState, useEffect } from 'react';
import { Map as MapIcon, Info, BookOpen } from 'lucide-react';
import { conceptualThesis } from '../data/bioContent';

const DiscordanceMap = ({ result }) => {
  const [quadrants, setQuadrants] = useState({ q1: [], q2: [], q3: [], q4: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/discordance');
        const json = await res.json();
        
        const q1 = []; const q2 = []; const q3 = []; const q4 = [];
        
        json.forEach(d => {
          const x = parseFloat(d.spillover_probability);
          const y = parseFloat(d.rg3_rg4_probability);
          if (x <= 0.5 && y >= 0.5) q1.push(d); // Top-Left: Low Spill, High Sev
          else if (x > 0.5 && y >= 0.5) q2.push(d); // Top-Right: High Spill, High Sev
          else if (x <= 0.5 && y < 0.5) q3.push(d); // Bottom-Left: Low Spill, Low Sev
          else if (x > 0.5 && y < 0.5) q4.push(d); // Bottom-Right: High Spill, Low Sev
        });

        setQuadrants({ q1, q2, q3, q4 });
      } catch (err) {
        console.error("Failed to load discordance data:", err);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const renderExamples = (viruses) => {
    const examples = viruses.slice(0, 5);
    return (
      <div className="absolute inset-0 bg-white/95 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-center items-center p-6 border border-stone-200 z-10 text-center">
        <h4 className="text-xs font-bold text-stone-500 uppercase tracking-widest mb-3">Example Pathogens</h4>
        <ul className="space-y-2">
          {examples.map((v, i) => (
            <li key={i} className="text-sm font-serif text-stone-800">{v.name}</li>
          ))}
          {viruses.length > 5 && <li className="text-xs text-stone-400 mt-2 font-medium">+{viruses.length - 5} more</li>}
        </ul>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-stone-200">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-serif font-semibold text-stone-800">The "Silent Reservoir" Map</h2>
            <p className="text-stone-500 text-sm mt-2 max-w-3xl leading-relaxed">
              This 2x2 Matrix visualizes the decoupling of ecological emergence (Spillover) and sociomedical containment (Risk Group). Hover over the <span className="font-medium text-yellow-700 bg-yellow-50 px-1 rounded">Regulatory Blindspot</span> quadrant to identify pathogens with high spillover capacity that are deprioritized by high-security biodefense frameworks.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-stone-200 min-h-[600px] flex flex-col relative overflow-hidden">
        {loading ? (
          <div className="flex-grow flex items-center justify-center">
            <div className="animate-pulse flex flex-col items-center">
              <MapIcon className="w-8 h-8 text-stone-300 mb-2" />
              <div className="text-stone-500 text-sm font-medium">Binning Pathogens into Archetypes...</div>
            </div>
          </div>
        ) : (
          <div className="flex-grow flex flex-col relative">
            {/* Axis Labels */}
            <div className="absolute -left-4 top-1/2 -translate-y-1/2 -rotate-90 text-xs font-bold text-stone-400 tracking-widest uppercase">Containment Priority</div>
            <div className="absolute bottom-[-16px] left-1/2 -translate-x-1/2 text-xs font-bold text-stone-400 tracking-widest uppercase">Spillover Potential</div>

            {/* Grid */}
            <div className="grid grid-cols-2 grid-rows-2 w-full h-full gap-4 p-8 relative flex-grow min-h-[500px]">
              
              {/* Q1: Top-Left (Low Spill, High Sev) */}
              <div className="group relative bg-stone-50 border border-stone-200 rounded-tl-3xl rounded-tr rounded-bl flex flex-col justify-center items-center text-center p-8 overflow-hidden transition-all hover:shadow-md">
                <div className="text-5xl font-serif text-stone-800 font-bold mb-2">{quadrants.q1.length}</div>
                <div className="text-xs font-bold text-stone-500 uppercase tracking-widest mb-2">Rare & Catastrophic</div>
                <p className="text-xs text-stone-500 max-w-xs">Limited ecological mobility, but extreme clinical consequence post-entry (e.g., Filoviruses).</p>
                {renderExamples(quadrants.q1)}
              </div>

              {/* Q2: Top-Right (High Spill, High Sev) */}
              <div className="group relative bg-orange-50/30 border border-orange-100 rounded-tr-3xl rounded-tl rounded-br flex flex-col justify-center items-center text-center p-8 overflow-hidden transition-all hover:shadow-md">
                <div className="text-5xl font-serif text-orange-800 font-bold mb-2">{quadrants.q2.length}</div>
                <div className="text-xs font-bold text-orange-700 uppercase tracking-widest mb-2">Acute Biosecurity Threats</div>
                <p className="text-xs text-orange-800/70 max-w-xs">Broad ecological access combined with severe clinical pathology (e.g., Nipah, Lassa).</p>
                {renderExamples(quadrants.q2)}
              </div>

              {/* Q3: Bottom-Left (Low Spill, Low Sev) */}
              <div className="group relative bg-lime-50/30 border border-lime-100 rounded-bl-3xl rounded-tl rounded-br flex flex-col justify-center items-center text-center p-8 overflow-hidden transition-all hover:shadow-md">
                <div className="text-5xl font-serif text-lime-800 font-bold mb-2">{quadrants.q3.length}</div>
                <div className="text-xs font-bold text-lime-700 uppercase tracking-widest mb-2">Manageable Baseline</div>
                <p className="text-xs text-lime-800/70 max-w-xs">Restricted ecological reach and manageable clinical outcomes.</p>
                {renderExamples(quadrants.q3)}
              </div>

              {/* Q4: Bottom-Right (High Spill, Low Sev) */}
              <div className="group relative bg-yellow-50 border-2 border-yellow-200 rounded-br-3xl rounded-tr rounded-bl flex flex-col justify-center items-center text-center p-8 overflow-hidden transition-all hover:shadow-lg hover:border-yellow-300">
                <div className="absolute top-4 right-4"><Info className="w-5 h-5 text-yellow-500" /></div>
                <div className="text-5xl font-serif text-yellow-800 font-bold mb-2">{quadrants.q4.length}</div>
                <div className="text-xs font-bold text-yellow-700 uppercase tracking-widest mb-2">The Regulatory Blindspot</div>
                <p className="text-xs text-yellow-800/70 max-w-xs">High ecological exposure rate but deprioritized containment due to clinical manageability or perceived genomic stability.</p>
                {renderExamples(quadrants.q4)}
              </div>

              {/* Current Evaluated Virus Marker */}
              {result && (() => {
                 const rawX = result.spillover_probability;
                 const rawY = result.rg_probabilities.RG3 + result.rg_probabilities.RG4;
                 
                 // Map raw probabilities to bounded visual coordinates (keeps dot away from 0, 0.5, 1.0 edges)
                 const getVisualCoord = (val) => {
                   if (val < 0.5) return 0.15 + (val * 0.5); // Maps [0, 0.5] to [0.15, 0.4]
                   return 0.65 + ((val - 0.5) * 0.5); // Maps [0.5, 1.0] to [0.65, 0.9]
                 };

                 return (
                 <div className="absolute top-8 left-8 right-8 bottom-8 pointer-events-none z-30">
                    <div 
                      className="absolute w-5 h-5 bg-blue-600 rounded-full shadow-[0_0_15px_rgba(37,99,235,0.6)] border-2 border-white flex items-center justify-center transition-all duration-700"
                      style={{
                        left: `${getVisualCoord(rawX) * 100}%`,
                        bottom: `${getVisualCoord(rawY) * 100}%`,
                        transform: 'translate(-50%, 50%)'
                      }}
                    >
                      <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-blue-900 text-white text-[10px] font-bold px-2 py-1 rounded whitespace-nowrap shadow-md">
                        Input Pathogen
                      </div>
                      <div className="absolute inset-0 rounded-full bg-blue-500 animate-ping opacity-75"></div>
                    </div>
                 </div>
                 );
              })()}

            </div>
          </div>
        )}
      </div>

      {/* The Conceptual Thesis Modals */}
      <section className="bg-stone-100 p-8 rounded-xl border border-stone-200 mt-8">
        <div className="flex items-center gap-2 mb-8">
          <BookOpen className="w-6 h-6 text-stone-400" />
          <h3 className="text-2xl font-serif font-bold text-stone-800">Research Findings: Conceptual Thesis</h3>
        </div>
        <div className="space-y-8">
          {conceptualThesis.map((thesis, index) => (
            <div key={index} className="bg-white p-8 rounded-lg shadow-sm border-l-4 border-l-lime-800 border-t border-r border-b border-stone-200">
              <h4 className="text-xl font-serif font-bold text-stone-800 mb-3">{thesis.title}</h4>
              <p className="text-stone-600 text-base leading-relaxed">{thesis.explanation}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default DiscordanceMap;
