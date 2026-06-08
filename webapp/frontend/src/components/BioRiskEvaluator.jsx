import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { AlertTriangle, Info, CheckCircle2, ShieldAlert, Server, Activity, Dna, HelpCircle, Network } from 'lucide-react';
import { genomeDescriptions, featureScorecard, dualScoreExplanation, confidenceLevels, spilloverLevels, globalPredictors } from '../data/bioContent';

const TAXONOMIC_FAMILIES = {
    0: "Adenoviridae", 1: "Alloherpesviridae", 2: "Amnoonviridae", 3: "Anelloviridae", 4: "Arenaviridae", 
    5: "Arteriviridae", 6: "Asfarviridae", 7: "Astroviridae", 8: "Baculoviridae", 9: "Birnaviridae", 
    10: "Bornaviridae", 11: "Caliciviridae", 12: "Circoviridae", 13: "Coronaviridae", 14: "Darmviridae", 
    15: "Dicistroviridae", 16: "Filoviridae", 17: "Flaviviridae", 18: "Hantaviridae", 19: "Hepaciviridae", 
    20: "Hepadnaviridae", 21: "Hepeviridae", 22: "Iridoviridae", 23: "Kitaviridae", 24: "Malacoherpesviridae", 
    25: "Matonaviridae", 26: "Nairoviridae", 27: "Nodaviridae", 28: "Orthoherpesviridae", 29: "Orthomyxoviridae", 
    30: "Papillomaviridae", 31: "Paramyxoviridae", 32: "Parvoviridae", 33: "Peribunyaviridae", 34: "Pestiviridae", 
    35: "Phenuiviridae", 36: "Picornaviridae", 37: "Pneumoviridae", 38: "Polyomaviridae", 39: "Poxviridae", 
    40: "Retroviridae", 41: "Rhabdoviridae", 42: "Sedoreoviridae", 43: "Spinareoviridae", 44: "Tobaniviridae", 
    45: "Togaviridae", 46: "Virgaviridae", 47: "unknown"
};

const SegmentedControl = ({ label, value, onChange }) => (
  <div className="flex flex-col">
    <span className="text-[10px] tracking-wider text-stone-500 uppercase mb-2 font-bold">{label}</span>
    <div className="flex bg-stone-200 rounded-full p-1 overflow-hidden shadow-sm h-11">
      <button 
        onClick={() => onChange(1)}
        className={`flex-1 flex items-center justify-center text-xs px-2 rounded-full font-bold transition-colors ${value === 1 ? 'bg-lime-800 text-white shadow-inner' : 'text-stone-500 hover:text-stone-700 hover:bg-stone-300'}`}
      >
        Yes
      </button>
      <button 
        onClick={() => onChange(null)}
        className={`flex-1 flex items-center justify-center text-xs px-2 rounded-full font-bold transition-colors ${value === null || isNaN(value) ? 'bg-stone-400 text-white shadow-inner' : 'text-stone-500 hover:text-stone-700 hover:bg-stone-300'}`}
      >
        ?
      </button>
      <button 
        onClick={() => onChange(0)}
        className={`flex-1 flex items-center justify-center text-xs px-2 rounded-full font-bold transition-colors ${value === 0 ? 'bg-orange-700 text-white shadow-inner' : 'text-stone-500 hover:text-stone-700 hover:bg-stone-300'}`}
      >
        No
      </button>
    </div>
  </div>
);

const BioRiskEvaluator = ({ result, setResult, explanation, setExplanation }) => {
  const [formData, setFormData] = useState({
    is_dna: 0,
    is_enveloped: 1,
    is_segmented: 0,
    is_vector_borne: 0,
    is_zoonotic: 1,
    infects_humans: 1,
    host_breadth: 5.0,
    genome_type_enc: 4,
    taxonomic_family_enc: 12
  });

  const getGenomeDesc = (enc) => {
    if (enc === null || isNaN(enc)) return null;
    const mapping = { 4: 'ssRNA_minus', 5: 'ssRNA_plus', 0: 'dsDNA', 1: 'dsRNA', 3: 'ssDNA' };
    const key = mapping[enc];
    return key ? genomeDescriptions[key] : null;
  };
  
  const [loading, setLoading] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  const handlePredict = async () => {
    setLoading(true);
    try {
      const pRes = await fetch('http://127.0.0.1:8000/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!pRes.ok) throw new Error("Predict request failed");
      const pData = await pRes.json();
      setResult(pData);

      const eRes = await fetch('http://127.0.0.1:8000/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!eRes.ok) throw new Error("Explain request failed");
      const eData = await eRes.json();
      setExplanation(eData);
    } catch (err) {
      console.error(err);
      setResult(null);
      setExplanation(null);
    }
    setLoading(false);
  };

  const formatFeatureLabel = (val) => {
    const map = {
      taxonomic_family_enc: "Taxonomic Lineage",
      genome_type_enc: "Genome Architecture",
      infects_humans: "Human Susceptibility",
      is_dna: "DNA Genome",
      is_enveloped: "Enveloped",
      is_segmented: "Segmented Genome",
      is_vector_borne: "Vector Borne",
      is_zoonotic: "Zoonotic",
      host_breadth: "Host Breadth"
    };
    return map[val] || val.replace(/_enc/g, '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const generateContainmentExplanation = () => {
    if (!result || !explanation) return null;
    const pRG = result.rg_prediction;
    const predictedKey = `RG${pRG}`;
    
    // 1. Primary Driver for assigned RG
    const currFeatures = explanation[predictedKey]?.features || [];
    const sortedCurr = [...currFeatures].sort((a, b) => b.shap_value - a.shap_value);
    const primaryDriver = sortedCurr[0];

    if (!primaryDriver || primaryDriver.shap_value <= 0) return (
      <div className="mt-2 pt-2 border-t border-stone-100 text-[11px] text-stone-600 leading-snug">
        Assigned via baseline risk prior across all 4 pathways.
      </div>
    );

    let dynamics = [];

    [1, 2, 3, 4].forEach(rgNum => {
      if (rgNum === pRG) return;
      const rgKey = `RG${rgNum}`;
      if (explanation[rgKey]) {
        const mitigator = [...explanation[rgKey].features].sort((a, b) => a.shap_value - b.shap_value)[0];
        if (mitigator && mitigator.shap_value < -0.01) {
           const bioText = mitigator.bio_translation?.instance_reason || '';
           const keyword = bioText.includes(':') ? bioText.split(':')[0].trim() : bioText;

           dynamics.push({
             shapPart: `RG${rgNum} rejected by ${formatFeatureLabel(mitigator.feature)} (${mitigator.shap_value.toFixed(2)})`,
             bioPart: keyword
           });
        }
      }
    });

    return (
      <div className="mt-2 pt-2 border-t border-stone-100 space-y-1.5">
        <p className="text-[11px] text-stone-600 leading-snug">
          <span className="font-semibold text-stone-800">Primary Driver:</span> {formatFeatureLabel(primaryDriver.feature)} (+{primaryDriver.shap_value.toFixed(2)})
        </p>
        {dynamics.length > 0 && (
          <div className="text-[10px] text-stone-500 leading-snug border-l-2 border-stone-200 pl-2">
            <span className="font-semibold text-stone-600 uppercase text-[9px] tracking-wider block mb-1">Cross-Pathway Rejection:</span> 
            <ul className="space-y-1">
              {dynamics.map((dyn, i) => (
                <li key={i} className="leading-snug text-stone-600">
                  <span className="font-semibold text-stone-700 bg-stone-100 px-1 py-0.5 rounded">{dyn.shapPart}</span>
                  <span className="ml-1 font-medium">{dyn.bioPart}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-stone-200 shadow-md rounded w-96 max-w-lg z-50 relative">
          <div className="flex justify-between items-start mb-2">
            <p className="font-serif font-bold text-base text-stone-800">{formatFeatureLabel(data.feature)}</p>
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${data.shap_value > 0 ? 'bg-lime-100 text-lime-800' : 'bg-orange-100 text-orange-800'}`}>
              SHAP: {data.shap_value > 0 ? '+' : ''}{data.shap_value.toFixed(4)}
            </span>
          </div>
          
          <div className="space-y-3">
            <div>
              <p className="text-[10px] font-bold text-stone-400 tracking-wider uppercase mb-0.5">Instance Evaluation</p>
              <p className="text-sm text-stone-700 leading-snug bg-stone-50 p-2 rounded border border-stone-100">{data.bio_translation.instance_reason}</p>
            </div>
            
            <div>
              <p className="text-[10px] font-bold text-stone-400 tracking-wider uppercase mb-0.5">Global Model Weight</p>
              <p className="text-xs text-stone-500 leading-snug">{data.bio_translation.global_reason}</p>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-stone-200">
        <h2 className="text-2xl font-serif font-semibold text-stone-800">The "Disease X" Evaluator</h2>
        <p className="text-stone-500 text-sm mt-2 max-w-4xl leading-relaxed">
          {dualScoreExplanation}
        </p>
      </div>

      {/* Command Bar */}
      <div className="bg-stone-50 border-b border-stone-200 py-8 px-6 rounded-lg shadow-sm mb-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Zone 1: The Binary Matrix */}
          <div className="lg:col-span-6 lg:border-r border-stone-200 lg:pr-8">
            <div className="grid grid-cols-3 gap-y-6 gap-x-6">
              <SegmentedControl label="DNA Genome" value={formData.is_dna} onChange={(v) => setFormData({...formData, is_dna: v})} />
              <SegmentedControl label="Enveloped" value={formData.is_enveloped} onChange={(v) => setFormData({...formData, is_enveloped: v})} />
              <SegmentedControl label="Segmented" value={formData.is_segmented} onChange={(v) => setFormData({...formData, is_segmented: v})} />
              <SegmentedControl label="Vector Borne" value={formData.is_vector_borne} onChange={(v) => setFormData({...formData, is_vector_borne: v})} />
              <SegmentedControl label="Zoonotic" value={formData.is_zoonotic} onChange={(v) => setFormData({...formData, is_zoonotic: v})} />
              <SegmentedControl label="Infects Humans" value={formData.infects_humans} onChange={(v) => setFormData({...formData, infects_humans: v})} />
            </div>
          </div>

          {/* Zone 2: Categoricals & Continua */}
          <div className="lg:col-span-4 flex flex-col gap-5 lg:pr-8 lg:border-r border-stone-200 justify-center">
            <div>
              <label className="block text-[10px] font-bold text-stone-500 uppercase tracking-wider mb-3">Host Breadth (Mammalian Taxa)</label>
              <input 
                type="range" min="1" max="20" 
                value={formData.host_breadth || 1} 
                onChange={e => setFormData({...formData, host_breadth: parseFloat(e.target.value)})}
                className="w-full accent-lime-800"
              />
              <div className="text-[10px] text-right text-stone-500 font-mono mt-2">{formData.host_breadth}</div>
            </div>
            <div className="flex gap-4 mt-2">
               <div className="flex-1">
                 <label className="block text-[10px] font-bold text-stone-500 uppercase tracking-wider mb-2">Genome Architecture</label>
                 <select
                   value={formData.genome_type_enc === null ? '' : formData.genome_type_enc}
                   onChange={e => setFormData({...formData, genome_type_enc: e.target.value === '' ? null : parseInt(e.target.value)})}
                   className="w-full h-11 px-3 border border-stone-200 rounded-xl text-xs font-medium bg-white focus:ring-1 focus:ring-lime-800 outline-none shadow-sm"
                 >
                   <option value="">Unknown (Null)</option>
                   <option value="4">ssRNA-</option>
                   <option value="5">ssRNA+</option>
                   <option value="0">dsDNA</option>
                   <option value="1">dsRNA</option>
                   <option value="3">ssDNA</option>
                 </select>
               </div>
               <div className="flex-1">
                 <label className="block text-[10px] font-bold text-stone-500 uppercase tracking-wider mb-2">Taxonomic Family</label>
                 <select
                   value={formData.taxonomic_family_enc === null ? '' : formData.taxonomic_family_enc}
                   onChange={e => setFormData({...formData, taxonomic_family_enc: e.target.value === '' ? null : parseInt(e.target.value)})}
                   className="w-full h-11 px-3 border border-stone-200 rounded-xl text-xs font-medium bg-white focus:ring-1 focus:ring-lime-800 outline-none shadow-sm"
                 >
                   <option value="">Unknown (Null)</option>
                   {Object.entries(TAXONOMIC_FAMILIES).map(([val, name]) => (
                     <option key={val} value={val}>{name}</option>
                   ))}
                 </select>
               </div>
            </div>
          </div>

          {/* Zone 3: The Action Zone */}
          <div className="lg:col-span-2 flex items-center justify-center pl-2">
            <button 
              onClick={handlePredict}
              disabled={loading}
              className="w-full h-full min-h-[100px] bg-stone-800 text-white rounded-2xl font-semibold tracking-wide text-sm hover:bg-stone-700 transition-colors disabled:opacity-50 shadow-md"
            >
              {loading ? 'Simulating...' : 'Evaluate Biological Hazard'}
            </button>
          </div>
        </div>
      </div>

        {/* Output Zone */}
        <div className="w-full space-y-6">
          {result && (
            <>
              {/* Top Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-5 rounded-lg shadow-sm border border-stone-200 flex flex-col justify-between">
                  <div className="text-xs text-stone-500 font-medium tracking-wide uppercase">Spillover Assessment</div>
                  <div className="mt-2">
                    {result.spillover_probability > 0.65 ? (
                      <span className="text-lg font-bold text-orange-700">HIGH ECOLOGICAL POTENTIAL</span>
                    ) : result.spillover_probability >= 0.35 ? (
                      <span className="text-lg font-bold text-yellow-700">MEDIUM / UNCERTAIN POTENTIAL</span>
                    ) : (
                      <span className="text-lg font-bold text-lime-800">LOWER ECOLOGICAL POTENTIAL</span>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-stone-600 leading-snug border-t border-stone-100 pt-2">
                    {result.spillover_probability > 0.65 ? spilloverLevels.High : result.spillover_probability >= 0.35 ? spilloverLevels.Medium : spilloverLevels.Low}
                  </div>
                </div>

                <div className="bg-white p-5 rounded-lg shadow-sm border border-stone-200 flex flex-col justify-between">
                  <div>
                    <div className="text-xs text-stone-500 font-medium tracking-wide uppercase">Containment Tier</div>
                    <div className="mt-1 flex items-baseline gap-2">
                      <span className="text-3xl font-serif text-stone-800">RG {result.rg_prediction}</span>
                    </div>
                    <div className="text-xs text-stone-400 mt-0.5">Highest prob: {(Math.max(...Object.values(result.rg_probabilities)) * 100).toFixed(1)}%</div>
                  </div>
                  {generateContainmentExplanation()}
                </div>

                <div className={`p-5 rounded-lg shadow-sm border ${result.confidence.score >= 70 ? 'bg-lime-50 border-lime-200' : result.confidence.score >= 45 ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'}`}>
                  <div className="text-xs font-medium tracking-wide uppercase flex items-center gap-1">
                    {result.confidence.score >= 70 ? <CheckCircle2 className="w-3 h-3 text-lime-700" /> : <AlertTriangle className="w-3 h-3 text-orange-700" />}
                    <span className={result.confidence.score >= 70 ? 'text-lime-800' : 'text-orange-800'}>Uncertainty Engine</span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className={`text-3xl font-serif ${result.confidence.score >= 70 ? 'text-lime-900' : 'text-orange-900'}`}>{result.confidence.score}%</span>
                  </div>
                  <div className="mt-2 text-xs text-stone-600 leading-snug">
                    {result.confidence.score >= 70 ? confidenceLevels.High : result.confidence.score >= 45 ? confidenceLevels.Moderate : confidenceLevels.Low}
                  </div>
                </div>
              </div>

              {/* SHAP Waterfall - Moved Above Scorecard */}
              {result && explanation && (
                <div className="bg-white p-6 rounded-lg shadow-sm border border-stone-200 mt-8">
                  <h3 className="font-serif text-2xl font-semibold text-stone-800 mb-2">Biological Translation (SHAP Pathways)</h3>
                  <p className="text-sm text-stone-500 mb-2">Hover over the bars to reveal the mechanistic translation of how each feature shifts the probability of requiring each Risk Group containment level.</p>
                  <div className="flex gap-4 mb-6 text-xs font-medium">
                    <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-lime-800 opacity-90"></div> Olive pushes probability UP</span>
                    <span className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-orange-800 opacity-90"></div> Terracotta pushes probability DOWN</span>
                  </div>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {["RG1", "RG2", "RG3", "RG4"].map(rg => (
                      <div key={rg} className="flex flex-col h-80 bg-stone-50 rounded-lg border border-stone-200 p-4 shadow-sm">
                        <h4 className="text-center font-serif font-bold text-stone-800 text-lg mb-2">{rg} Pathway</h4>
                        <div className="flex-grow">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={explanation[rg]?.features} layout="vertical" margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                              <XAxis type="number" hide />
                              <YAxis 
                                dataKey="feature" 
                                type="category" 
                                axisLine={false} 
                                tickLine={false} 
                                width={140}
                                tick={{ fontSize: 11, fill: '#57534E', fontWeight: 600, textAnchor: 'end' }} 
                                tickFormatter={formatFeatureLabel}
                              />
                              <Tooltip content={<CustomTooltip />} cursor={{ fill: '#E7E5E4' }} wrapperStyle={{ zIndex: 1000, pointerEvents: 'auto' }} />
                              <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
                                {explanation[rg]?.features?.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.shap_value > 0 ? '#3F6212' : '#C2410C'} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Biological Feature Scorecard */}
              <div className="bg-white p-6 rounded-lg shadow-sm border border-stone-200 mt-8">
                <h3 className="font-serif text-2xl font-semibold text-stone-800 mb-2">Biological Feature Scorecard</h3>
                <p className="text-sm text-stone-500 mb-6">A unified matrix combining baseline traits, global structural weights, and instance-specific SHAP explanations.</p>
                <div className="grid grid-cols-1 gap-6">
                  {Object.keys(featureScorecard).map(key => {
                    const val = formData[key];
                    let mappedVal = val === null ? null : val;
                    if (key === 'host_breadth' && val !== null) {
                      mappedVal = val > 5 ? 1 : 0;
                    } else if (key === 'taxonomic_family_enc' && val !== null) {
                      mappedVal = featureScorecard[key][val] ? val : 'default';
                    }
                    const data = mappedVal !== null ? featureScorecard[key][mappedVal] : null;

                    const keyToGlobal = {
                      taxonomic_family_enc: "Taxonomic Family",
                      genome_type_enc: "Genome Type",
                      infects_humans: "Infects Humans",
                      is_dna: "DNA/RNA Status",
                      is_enveloped: "Enveloped",
                      is_segmented: "Segmented Genome",
                      is_vector_borne: "Vector-borne Transmission",
                      is_zoonotic: "Zoonotic Origin",
                      host_breadth: "Host Breadth"
                    };
                    const globalTitle = keyToGlobal[key];
                    const globalPred = globalPredictors.find(p => p.feature === globalTitle);

                    let shapFeature = null;
                    if (result && explanation) {
                       shapFeature = explanation[`RG${result.rg_prediction}`]?.features?.find(f => f.feature === key);
                    }
                    
                    return (
                      <div key={key} className={`p-6 rounded-lg border shadow-sm ${data ? (data.signal.includes('HIGH') || data.signal.includes('PRIMARY') ? 'bg-orange-50/30 border-orange-200' : 'bg-lime-50/30 border-lime-200') : 'bg-stone-50 border-dashed border-stone-200'}`}>
                        <div className="flex justify-between items-start mb-4 border-b border-stone-200 pb-3">
                          <div>
                            <h4 className="text-base font-bold text-stone-800 uppercase tracking-widest">{formatFeatureLabel(key)}</h4>
                            {globalPred && <div className="text-[11px] text-stone-500 font-bold mt-1 tracking-wide">GLOBAL WEIGHT: {globalPred.weight}</div>}
                          </div>
                          {shapFeature && (
                            <span className={`text-xs px-3 py-1.5 rounded font-bold shadow-sm ${shapFeature.shap_value > 0 ? 'bg-lime-100 text-lime-800' : 'bg-orange-100 text-orange-800'}`}>
                              SHAP: {shapFeature.shap_value > 0 ? '+' : ''}{shapFeature.shap_value.toFixed(4)}
                            </span>
                          )}
                        </div>

                        {data ? (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-2">
                            <div>
                              <p className="text-[10px] font-bold text-stone-400 tracking-wider uppercase mb-1.5 flex items-center gap-1.5">
                                <Activity className="w-3 h-3" /> Instance Evaluation
                              </p>
                              <div className="text-sm text-stone-700 leading-relaxed bg-white p-5 rounded-lg border border-stone-100 shadow-sm h-full">
                                <span className="font-bold text-stone-800 block mb-2 text-base font-serif">{data.value}</span>
                                <p>{data.explanation}</p>
                                {shapFeature && shapFeature.bio_translation.instance_reason && (
                                  <p className="mt-4 pt-4 border-t border-stone-100 text-stone-600 font-medium">
                                    {shapFeature.bio_translation.instance_reason}
                                  </p>
                                )}
                              </div>
                            </div>
                            
                            {globalPred && (
                              <div>
                                <p className="text-[10px] font-bold text-stone-400 tracking-wider uppercase mb-1.5 flex items-center gap-1.5">
                                  <Network className="w-3 h-3" /> Global Baseline Insight
                                </p>
                                <div className="text-sm text-stone-600 leading-relaxed bg-stone-50 p-5 rounded-lg border border-stone-100 h-full">
                                  <p>{globalPred.reason}</p>
                                  {shapFeature && shapFeature.bio_translation.global_reason && (
                                    <p className="mt-4 pt-4 border-t border-stone-200 text-stone-500 italic">
                                      {shapFeature.bio_translation.global_reason}
                                    </p>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="flex flex-col items-center justify-center text-stone-400 py-8">
                            <HelpCircle className="w-8 h-8 mb-2 opacity-50" />
                            <span className="text-sm font-medium">Data Gap (Unknown Parameter)</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Raw JSON Transparency */}
              <div className="mt-4">
                <button 
                  onClick={() => setShowRaw(!showRaw)}
                  className="text-xs text-stone-500 hover:text-stone-800 flex items-center gap-1 transition-colors"
                >
                  <Server className="w-3 h-3" /> {showRaw ? 'Hide Raw Model Output' : 'View Raw Model Output'}
                </button>
                {showRaw && (
                  <div className="mt-2 bg-stone-900 rounded p-4 overflow-x-auto">
                    <pre className="text-[10px] text-stone-300 font-mono">
                      {JSON.stringify(result.raw_json, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </>
          )}

          {!result && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-stone-400 p-12 border-2 border-dashed border-stone-200 rounded-lg">
              <ShieldAlert className="w-12 h-12 mb-3 text-stone-300" />
              <p className="font-medium text-stone-600">No Evaluation Rendered</p>
              <p className="text-sm mt-1 text-center">Adjust the parameters on the left and click "Evaluate Biological Hazard" to simulate.</p>
            </div>
          )}
        </div>
      

    </div>
  );
};

export default BioRiskEvaluator;
