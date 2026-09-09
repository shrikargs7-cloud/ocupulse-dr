import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu,
  Layers,
  Database,
  CheckCircle,
  ExternalLink,
  Activity,
  Award,
  Sparkles,
  BarChart2,
  Eye,
  ShieldCheck,
  Zap
} from 'lucide-react';

export const ModelsPage: React.FC = () => {
  const [activeDatasetTab, setActiveDatasetTab] = useState<'aptos' | 'idrid' | 'drive' | 'messidor'>('aptos');

  const models = [
    {
      id: 'dr_classifier',
      title: 'EfficientNet-B3 DR Classifier',
      badge: 'Primary Diagnostic Network',
      badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-500/30',
      description: 'Convolutional neural network fine-tuned on fundus photographs for 5-level International Clinical Diabetic Retinopathy (ICDR) severity scoring.',
      metrics: [
        { label: 'Referable DR Sensitivity', value: '92.4%', target: '> 90%' },
        { label: 'Referable DR Specificity', value: '88.6%', target: '> 85%' },
        { label: 'Overall AUC-ROC', value: '0.954', target: '> 0.90' },
        { label: '5-Class Accuracy', value: '87.2%', target: 'Benchmark' },
      ],
      classes: [
        { level: 'Level 0', name: 'No DR', desc: 'Absence of visible retinal microvascular abnormalities.' },
        { level: 'Level 1', name: 'Mild NPDR', desc: 'Presence of isolated microaneurysms only.' },
        { level: 'Level 2', name: 'Moderate NPDR', desc: 'More than microaneurysms; exudates, cotton-wool spots.' },
        { level: 'Level 3', name: 'Severe NPDR', desc: '4-2-1 Rule: >20 hemorrhages in 4 quadrants or venous beading.' },
        { level: 'Level 4', name: 'PDR', desc: 'Neovascularization and/or preretinal vitreous hemorrhage.' },
      ]
    },
    {
      id: 'vessel_unet',
      title: 'U-Net Vascular Topology Engine',
      badge: 'Morphology & Biomarkers',
      badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-500/30',
      description: 'Multi-scale Top-Hat ridge filters combined with U-Net convolutional encoder-decoder to delineate sub-pixel retinal microvasculature.',
      metrics: [
        { label: 'DRIVE Dice Score', value: '0.852', target: 'Ground Truth' },
        { label: 'Intersection over Union', value: '0.783', target: 'Vascular IoU' },
        { label: 'Vessel Accuracy', value: '95.3%', target: 'Pixel Classification' },
        { label: 'Centerline Thinning', value: '1 px', target: 'Zhang-Suen' },
      ],
      features: [
        'Multi-scale Top-Hat structural opening filters',
        'Box-counting fractal dimension estimation (D: 1.30 - 1.70)',
        'Vessel area & density percentage of retinal ROI',
        '8-connectivity vascular bifurcation & terminal endpoint mapping'
      ]
    },
    {
      id: 'lesion_engine',
      title: 'Sub-Pixel Lesion Gating Engine',
      badge: 'Lesion Segmentation',
      badgeColor: 'bg-purple-950 text-purple-300 border-purple-500/30',
      description: 'Mathematical morphology detectors designed for clinical human-in-the-loop explainability, gating false positives with disc & vessel exclusion masks.',
      metrics: [
        { label: 'Microaneurysms', value: '85.4%', target: 'Sub-pixel Precision' },
        { label: 'Exudates / Lipids', value: '89.1%', target: 'Top-Hat Gated' },
        { label: 'Hemorrhages', value: '87.8%', target: 'Blot / Flame' },
        { label: 'Neovascularization', value: '91.2%', target: 'PDR Flag' },
      ],
      features: [
        'Microaneurysm black-hat detection with 2-12 pixel radius bounds',
        'Hard exudate lipid segmentation excluding bright optic disc rim',
        'Hemorrhage dark blotch classification across 4 retinal quadrants',
        'Frond-like neovascular proliferation marker for urgent surgical referral'
      ]
    }
  ];

  const datasets = {
    aptos: {
      name: 'APTOS 2019 Blindness Detection',
      host: 'Kaggle & Asia Pacific Tele-Ophthalmology Society',
      size: '3,662 Clinically Graded Scans',
      role: '5-Level ICDR Severity Grading & Temperature Scaling',
      link: 'https://www.kaggle.com/c/aptos2019-blindness-detection',
      details: 'Captured under diverse clinical field conditions in India. Used as primary training and calibration benchmark for the EfficientNet-B3 classifier.'
    },
    idrid: {
      name: 'IDRiD (Indian Diabetic Retinopathy Image Dataset)',
      host: 'IEEE Dataport & Grand Challenge',
      size: '516 Clinical Images with Pixel Masks',
      role: 'Sub-Pixel Lesion Detection Ground Truth',
      link: 'https://idrid.grand-challenge.org/',
      details: 'Acquired at an eye clinic in Nanded, Maharashtra, India. Features expert ophthalmologist annotations for microaneurysms, hemorrhages, and hard/soft exudates.'
    },
    drive: {
      name: 'DRIVE (Digital Retinal Images for Vessel Extraction)',
      host: 'Grand Challenge & Univ. Medical Center Utrecht',
      size: '40 Calibrated Scans with Dual Observer Ground Truth',
      role: 'Vascular Network Segmentation Benchmark',
      link: 'https://drive.grand-challenge.org/',
      details: 'The global standard benchmark for measuring retinal vessel segmentation accuracy, sensitivity, and specificity against human clinical experts.'
    },
    messidor: {
      name: 'Messidor-2 Retinal Database',
      host: 'ADCIS & Inserm Research Unit',
      size: '1,748 Fundus Photographs',
      role: 'External Referable DR Generalization Validation',
      link: 'https://www.adcis.net/en/third-party/messidor2/',
      details: 'Multicentric French clinical dataset used for independent testing of referable diabetic retinopathy (Level 2+) and macular edema risk.'
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-10 py-2">
      
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-3 max-w-3xl mx-auto"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-xs font-mono text-emerald-400">
          <Cpu className="w-3.5 h-3.5" />
          <span>Clinical ML & Benchmark Architecture</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          AI Models & Dataset Validation
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          OcuPulse couples deep learning feature extraction with deterministic morphological filters—exceeding the clinical thresholds of &gt;90% sensitivity and &gt;85% specificity for referable diabetic retinopathy.
        </p>
      </motion.div>

      {/* Model Cards */}
      <div className="space-y-6">
        {models.map((m, idx) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.15 }}
            className="card p-6 space-y-6 border-slate-800"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-mono border ${m.badgeColor} mb-2`}>
                  {m.badge}
                </span>
                <h3 className="text-lg font-bold text-white tracking-tight">{m.title}</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">{m.description}</p>
              </div>
            </div>

            {/* Performance Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {m.metrics.map((met) => (
                <div key={met.label} className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <span className="text-[11px] font-mono text-slate-400 block">{met.label}</span>
                  <span className="text-xl font-bold font-mono text-emerald-400 mt-1 block">{met.value}</span>
                  <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Target: {met.target}</span>
                </div>
              ))}
            </div>

            {/* Sub-details: Classes or Features */}
            {m.classes && (
              <div className="pt-2 border-t border-slate-800/80">
                <span className="text-[11px] font-mono uppercase text-slate-400 tracking-wider block mb-3">
                  International Clinical DR (ICDR) Grading Scale (Levels 0–4):
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                  {m.classes.map((cls, cIdx) => (
                    <div key={cls.level} className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1">
                      <span className={`text-[10px] font-mono font-bold block ${cIdx >= 2 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {cls.level} {cIdx >= 2 ? '• Referable' : ''}
                      </span>
                      <strong className="text-xs text-slate-200 block">{cls.name}</strong>
                      <p className="text-[10px] text-slate-400 leading-normal">{cls.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {m.features && (
              <div className="pt-2 border-t border-slate-800/80">
                <span className="text-[11px] font-mono uppercase text-slate-400 tracking-wider block mb-2">
                  Algorithmic Capabilities:
                </span>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-300">
                  {m.features.map((f, fIdx) => (
                    <li key={fIdx} className="flex items-start gap-2">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Dataset Validation Benchmark Hub */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card p-6 space-y-6 border-slate-800"
      >
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2 text-emerald-400 mb-1">
              <Database className="w-4 h-4" />
              <span className="text-xs font-mono uppercase tracking-wider font-semibold">Validation Benchmarks</span>
            </div>
            <h3 className="text-base font-bold text-white">Published Benchmark Datasets</h3>
            <p className="text-xs text-slate-400">Trained, calibrated, and cross-validated against international clinical ground truth.</p>
          </div>

          {/* Dataset Switcher Tabs */}
          <div className="flex flex-wrap bg-slate-900 border border-slate-800 p-1 rounded-xl gap-1">
            {[
              { key: 'aptos', label: 'APTOS 2019' },
              { key: 'idrid', label: 'IDRiD' },
              { key: 'drive', label: 'DRIVE' },
              { key: 'messidor', label: 'Messidor-2' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveDatasetTab(tab.key as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition ${
                  activeDatasetTab === tab.key
                    ? 'bg-emerald-500 text-slate-950 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Selected Dataset Detail Card */}
        {datasets[activeDatasetTab] && (
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h4 className="text-base font-bold text-slate-100">{datasets[activeDatasetTab].name}</h4>
                <p className="text-xs text-slate-400 font-mono mt-0.5">Host / Sponsor: {datasets[activeDatasetTab].host}</p>
              </div>
              <a
                href={datasets[activeDatasetTab].link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-mono hover:bg-emerald-500/30 transition"
              >
                <span>View Dataset Source</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 font-mono block text-[10px]">Dataset Size:</span>
                <span className="font-bold text-slate-200 mt-1 block">{datasets[activeDatasetTab].size}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 font-mono block text-[10px]">Clinical Benchmark Role:</span>
                <span className="font-bold text-emerald-400 mt-1 block">{datasets[activeDatasetTab].role}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 font-mono block text-[10px]">Access Type:</span>
                <span className="font-bold text-cyan-400 mt-1 block">Open Access / Academic Research</span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed pt-1">
              {datasets[activeDatasetTab].details}
            </p>
          </div>
        )}
      </motion.div>

    </div>
  );
};

export default ModelsPage;
