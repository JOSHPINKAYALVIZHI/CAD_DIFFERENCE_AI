import React, { useState, useRef, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  AlertCircle, 
  Eye, 
  Settings, 
  Activity, 
  Grid, 
  Image as ImageIcon,
  CheckCircle,
  HelpCircle,
  Sparkles,
  Info,
  Maximize2
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [previewA, setPreviewA] = useState(null);
  const [previewB, setPreviewB] = useState(null);
  
  const [minArea, setMinArea] = useState(70);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  
  const [viewMode, setViewMode] = useState('color_diff');
  const [selectedRegionId, setSelectedRegionId] = useState(null);
  
  const [splitPosition, setSplitPosition] = useState(50);
  const [isDraggingSplit, setIsDraggingSplit] = useState(false);
  const splitContainerRef = useRef(null);

  // File Upload Handlers
  const handleFileA = (file) => {
    if (!file) return;
    setFileA(file);
    if (file.type === 'application/pdf') {
      setPreviewA('pdf');
    } else {
      setPreviewA(URL.createObjectURL(file));
    }
  };

  const handleFileB = (file) => {
    if (!file) return;
    setFileB(file);
    if (file.type === 'application/pdf') {
      setPreviewB('pdf');
    } else {
      setPreviewB(URL.createObjectURL(file));
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e, target) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      if (target === 'A') handleFileA(files[0]);
      if (target === 'B') handleFileB(files[0]);
    }
  };

  // Compare Pipeline Execution
  const triggerCompare = async () => {
    if (!fileA || !fileB) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedRegionId(null);
    
    const formData = new FormData();
    formData.append('image_a', fileA);
    formData.append('image_b', fileB);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/compare?min_area=${minArea}`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Drawing comparison pipeline failed.');
      }
      
      const data = await response.json();
      setResult(data);
      setViewMode('color_diff');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Split view slider handlers
  const handleSplitMove = (clientX) => {
    if (!splitContainerRef.current) return;
    const rect = splitContainerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSplitPosition(percentage);
  };

  const handleMouseMove = (e) => {
    if (isDraggingSplit) {
      handleSplitMove(e.clientX);
    }
  };

  const handleTouchMove = (e) => {
    if (isDraggingSplit && e.touches.length > 0) {
      handleSplitMove(e.touches[0].clientX);
    }
  };

  useEffect(() => {
    const handleMouseUp = () => setIsDraggingSplit(false);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('touchend', handleMouseUp);
    return () => {
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, [isDraggingSplit]);

  // Determine current image to render in viewer
  const getViewerImage = () => {
    if (!result) return null;
    const viz = result.visualizations;
    switch (viewMode) {
      case 'ref': return `${API_BASE}${viz.annotated_ref}`;
      case 'cmp': return `${API_BASE}${viz.annotated_cmp}`;
      case 'color_diff': return `${API_BASE}${viz.color_diff}`;
      case 'blend': return `${API_BASE}${viz.blend_overlay}`;
      default: return `${API_BASE}${viz.color_diff}`;
    }
  };

  return (
    <div className="app-container">
      {/* Premium Header */}
      <header className="app-header">
        <div className="brand-section">
          <Activity size={24} color="#3b82f6" />
          <h1 className="brand-title">CAD Diff AI</h1>
          <span className="brand-badge">v1.0.0</span>
        </div>
        <div className="slider-container">
          <Settings size={16} />
          <label htmlFor="min-area-slider">Noise Limit: {minArea}px</label>
          <input 
            id="min-area-slider"
            type="range" 
            min="10" 
            max="300" 
            value={minArea} 
            onChange={(e) => setMinArea(parseInt(e.target.value))} 
            className="slider-input"
          />
        </div>
      </header>

      {/* Main Workspace */}
      <main className="main-content">
        
        {/* Upload Panel */}
        <div className="upload-grid fade-in">
          {/* Card A: Reference Drawing */}
          <div 
            className="card upload-zone"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, 'A')}
          >
            <input 
              type="file" 
              accept=".png,.jpg,.jpeg,.pdf" 
              onChange={(e) => handleFileA(e.target.files[0])}
              className="upload-input" 
              id="upload-a"
            />
            {fileA ? (
              <div className="file-preview">
                {previewA === 'pdf' ? (
                  <FileText size={64} color="#3b82f6" />
                ) : (
                  <img src={previewA} alt="Reference Preview" className="thumbnail" />
                )}
                <p style={{ fontWeight: 600, fontSize: '0.95rem' }}>{fileA.name}</p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  Reference Image (A) Loaded
                </p>
              </div>
            ) : (
              <>
                <Upload size={40} color="var(--text-secondary)" />
                <p style={{ fontWeight: 600 }}>Reference Image (A)</p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  Drag & drop or click to upload PDF/JPG/PNG
                </p>
              </>
            )}
          </div>

          {/* Card B: Comparison Drawing */}
          <div 
            className="card upload-zone"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, 'B')}
          >
            <input 
              type="file" 
              accept=".png,.jpg,.jpeg,.pdf" 
              onChange={(e) => handleFileB(e.target.files[0])}
              className="upload-input" 
              id="upload-b"
            />
            {fileB ? (
              <div className="file-preview">
                {previewB === 'pdf' ? (
                  <FileText size={64} color="#10b981" />
                ) : (
                  <img src={previewB} alt="Comparison Preview" className="thumbnail" />
                )}
                <p style={{ fontWeight: 600, fontSize: '0.95rem' }}>{fileB.name}</p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  Comparison Image (B) Loaded
                </p>
              </div>
            ) : (
              <>
                <Upload size={40} color="var(--text-secondary)" />
                <p style={{ fontWeight: 600 }}>Comparison Image (B)</p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  Drag & drop or click to upload PDF/JPG/PNG
                </p>
              </>
            )}
          </div>
        </div>

        {/* Trigger Button */}
        <div className="compare-action-panel fade-in">
          <button 
            className="btn" 
            onClick={triggerCompare} 
            disabled={!fileA || !fileB || loading}
          >
            {loading ? 'Processing Drawings...' : 'Detect Differences'}
          </button>
          {!fileA || !fileB ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Upload both images or PDF files to activate comparison analysis.
            </p>
          ) : null}
        </div>

        {/* Error Handling */}
        {error && (
          <div className="card fade-in" style={{ borderColor: 'var(--color-danger)', background: 'rgba(239, 68, 68, 0.05)', marginBottom: '2rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <AlertCircle color="var(--color-danger)" />
            <div>
              <p style={{ fontWeight: 600, color: 'var(--color-danger)' }}>Pipeline Error</p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{error}</p>
            </div>
          </div>
        )}

        {/* Loader Overlay */}
        {loading && (
          <div className="card loader-overlay fade-in">
            <div className="spinner"></div>
            <p style={{ fontWeight: 600 }}>Analyzing CAD layouts...</p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '400px', textAlign: 'center' }}>
              We are aligning drawing details via ORB homography, computing pixel-level differences, and generating an automated AI change summary.
            </p>
          </div>
        )}

        {/* Analysis Results Display */}
        {result && (
          <div className="fade-in">
            
            {/* 1. KPIs Section */}
            <div className="kpi-grid">
              <div className="kpi-card">
                <div className="kpi-icon-wrapper">
                  <Grid size={20} color="#3b82f6" />
                </div>
                <div className="kpi-info">
                  <span className="kpi-value">{result.statistics.total_regions}</span>
                  <span className="kpi-label">Modified Regions</span>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-icon-wrapper">
                  <Activity size={20} color="#10b981" />
                </div>
                <div className="kpi-info">
                  <span className="kpi-value">{result.statistics.change_percentage}%</span>
                  <span className="kpi-label">Drawing Modified Area</span>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-icon-wrapper">
                  <ImageIcon size={20} color="#f59e0b" />
                </div>
                <div className="kpi-info">
                  <span className="kpi-value">{(result.similarity_score * 100).toFixed(1)}%</span>
                  <span className="kpi-label">Structural Similarity</span>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-icon-wrapper">
                  <CheckCircle size={20} color="#06b6d4" />
                </div>
                <div className="kpi-info">
                  <span className="kpi-value" style={{ textTransform: 'capitalize' }}>
                    {result.status === 'success' ? 'Aligned' : 'Raw'}
                  </span>
                  <span className="kpi-label">Alignment Registration</span>
                </div>
              </div>
            </div>

            {/* 2. Visualizer Layout (Viewer + Details Panel) */}
            <div className="visualizer-layout">
              
              {/* Left Column: Image Canvas */}
              <div className="visualizer-viewer">
                <div className="viewer-header">
                  <h3 style={{ fontWeight: 600 }}>Workspace Preview</h3>
                  <div className="view-controls">
                    <button 
                      className={`view-btn ${viewMode === 'color_diff' ? 'active' : ''}`}
                      onClick={() => setViewMode('color_diff')}
                    >
                      Difference Map
                    </button>
                    <button 
                      className={`view-btn ${viewMode === 'split' ? 'active' : ''}`}
                      onClick={() => setViewMode('split')}
                    >
                      Split Slider
                    </button>
                    <button 
                      className={`view-btn ${viewMode === 'blend' ? 'active' : ''}`}
                      onClick={() => setViewMode('blend')}
                    >
                      Blend Overlay
                    </button>
                    <button 
                      className={`view-btn ${viewMode === 'ref' ? 'active' : ''}`}
                      onClick={() => setViewMode('ref')}
                    >
                      Ref (A)
                    </button>
                    <button 
                      className={`view-btn ${viewMode === 'cmp' ? 'active' : ''}`}
                      onClick={() => setViewMode('cmp')}
                    >
                      Comp (B)
                    </button>
                  </div>
                </div>

                <div className="viewer-canvas">
                  {viewMode === 'split' ? (
                    <div 
                      className="split-viewer"
                      ref={splitContainerRef}
                      onMouseMove={handleMouseMove}
                      onTouchMove={handleTouchMove}
                    >
                      {/* Before (Ref Image) */}
                      <div 
                        className="split-layer split-layer-before"
                        style={{ width: `${splitPosition}%` }}
                      >
                        <img 
                          src={`${API_BASE}${result.visualizations.annotated_ref}`} 
                          alt="Before" 
                        />
                      </div>
                      
                      {/* After (Aligned Comp Image) */}
                      <div className="split-layer split-layer-after">
                        <img 
                          src={`${API_BASE}${result.visualizations.annotated_cmp}`} 
                          alt="After" 
                        />
                      </div>

                      {/* Split Divider Slider Line */}
                      <div 
                        className="split-slider"
                        style={{ left: `${splitPosition}%` }}
                        onMouseDown={() => setIsDraggingSplit(true)}
                        onTouchStart={() => setIsDraggingSplit(true)}
                      >
                        <div className="split-slider-button">
                          ↔
                        </div>
                      </div>
                    </div>
                  ) : (
                    <img 
                      src={getViewerImage()} 
                      alt="Visualization View" 
                      className="canvas-img"
                    />
                  )}
                </div>
              </div>

              {/* Right Column: AI Summary & Stats Details */}
              <div className="details-panel">
                
                {/* AI Summary Block */}
                <div className="summary-box">
                  <div className="summary-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Sparkles size={16} />
                      <span>AI Change Summary</span>
                    </div>
                    {result.session_id && (
                      <button 
                        className="btn" 
                        style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', borderRadius: '4px', boxShadow: 'none' }}
                        onClick={() => window.open(`${API_BASE}/api/v1/compare/${result.session_id}/report`, '_blank')}
                      >
                        PDF Report
                      </button>
                    )}
                  </div>
                  <p style={{ marginTop: '0.5rem' }}>{result.summary}</p>
                </div>

                {/* Helpful Legend Box */}
                <div className="card" style={{ padding: '1rem', background: 'var(--bg-tertiary)' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
                    <Info size={14} /> Legend (Difference Map)
                  </h4>
                  <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ width: '12px', height: '12px', background: 'var(--color-danger)', borderRadius: '2px' }}></span>
                      <span>Removed Content (In A only)</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ width: '12px', height: '12px', background: 'var(--color-success)', borderRadius: '2px' }}></span>
                      <span>Added Content (In B only)</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ width: '12px', height: '12px', background: '#3b82f6', borderRadius: '2px' }}></span>
                      <span>Modified / Shifted Line-work</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 3. Regions Table */}
            <div className="regions-table-container">
              <table className="regions-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Location</th>
                    <th>Severity</th>
                    <th>Area (pixels)</th>
                    <th>Bounding Box [x, y, w, h]</th>
                    <th>Visual Comparison (Before vs After)</th>
                  </tr>
                </thead>
                <tbody>
                  {result.statistics.regions.map((r) => (
                    <tr 
                      key={r.id} 
                      className={selectedRegionId === r.id ? 'selected' : ''}
                      onClick={() => {
                        setSelectedRegionId(r.id);
                        setViewMode('ref'); // Toggles view to Ref so they can see boxes
                      }}
                    >
                      <td style={{ fontWeight: 700 }}>#{r.id}</td>
                      <td style={{ textTransform: 'capitalize' }}>{r.location.replace('-', ' ')}</td>
                      <td>
                        <span className={`badge badge-${r.severity}`}>
                          {r.severity}
                        </span>
                      </td>
                      <td>{r.area.toLocaleString()} px²</td>
                      <td style={{ fontFamily: 'monospace', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        [{r.bbox.join(', ')}]
                      </td>
                      <td>
                        {r.crop_ref_url && r.crop_cmp_url ? (
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Ref (A)</div>
                              <img src={`${API_BASE}${r.crop_ref_url}`} alt="Ref Crop" style={{ maxHeight: '50px', maxWidth: '80px', border: '1px solid var(--border-color)', borderRadius: '2px', background: 'white' }} />
                            </div>
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Comp (B)</div>
                              <img src={`${API_BASE}${r.crop_cmp_url}`} alt="Comp Crop" style={{ maxHeight: '50px', maxWidth: '80px', border: '1px solid var(--border-color)', borderRadius: '2px', background: 'white' }} />
                            </div>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>N/A</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          </div>
        )}

      </main>
    </div>
  );
}

export default App;
