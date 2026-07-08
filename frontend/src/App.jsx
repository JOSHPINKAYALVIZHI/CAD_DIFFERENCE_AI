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
  Maximize2,
  MessageSquare,
  Send
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [previewA, setPreviewA] = useState(null);
  const [previewB, setPreviewB] = useState(null);
  
  const [minArea, setMinArea] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  
  const [viewMode, setViewMode] = useState('color_diff');
  const [selectedRegionId, setSelectedRegionId] = useState(null);
  
  const [splitPosition, setSplitPosition] = useState(50);
  const [isDraggingSplit, setIsDraggingSplit] = useState(false);
  const [blendOpacity, setBlendOpacity] = useState(50);
  const [sidebarTab, setSidebarTab] = useState('info');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef(null);
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
    setChatHistory([]);
    setSidebarTab('info');
    
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
      if (minArea === 0 && data.statistics.detected_noise_limit) {
        setMinArea(data.statistics.detected_noise_limit);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const sendChatMessage = async (messageText) => {
    const textToSend = messageText || chatInput;
    if (!textToSend.trim() || chatLoading || !result?.session_id) return;
    
    const userMsg = { role: 'user', content: textToSend };
    const updatedHistory = [...chatHistory, userMsg];
    setChatHistory(updatedHistory);
    setChatInput('');
    setChatLoading(true);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/compare/${result.session_id}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          history: chatHistory.map(h => ({ role: h.role, content: h.content }))
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch AI assistant reply.');
      }
      
      const data = await response.json();
      setChatHistory([...updatedHistory, { role: 'model', content: data.response }]);
    } catch (err) {
      setChatHistory([...updatedHistory, { role: 'model', content: `Error: ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, chatLoading]);

  const renderMessageContent = (content) => {
    if (typeof content !== 'string') return content;
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      let cleanLine = line.trim();
      let isBullet = false;
      if (cleanLine.startsWith('*') || cleanLine.startsWith('-')) {
        isBullet = true;
        cleanLine = cleanLine.substring(1).trim();
      }
      
      const parts = cleanLine.split('**');
      const parsedLine = parts.map((part, i) => {
        if (i % 2 === 1) {
          return <strong key={i} style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{part}</strong>;
        }
        return part;
      });
      
      if (isBullet) {
        return (
          <div key={idx} style={{ display: 'flex', gap: '0.4rem', margin: '0.25rem 0', paddingLeft: '0.25rem', alignItems: 'flex-start' }}>
            <span style={{ color: '#3b82f6', marginTop: '0.15rem', fontSize: '0.8rem' }}>•</span>
            <span style={{ flex: 1 }}>{parsedLine}</span>
          </div>
        );
      }
      
      return <div key={idx} style={{ margin: '0.25rem 0' }}>{parsedLine}</div>;
    });
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
          <label htmlFor="min-area-slider">
            Noise Limit: {minArea === 0 ? 'Auto-Detect' : `${minArea}px`}
          </label>
          <input 
            id="min-area-slider"
            type="range" 
            min="10" 
            max="300" 
            value={minArea === 0 ? 70 : minArea} 
            onChange={(e) => setMinArea(parseInt(e.target.value))} 
            className="slider-input"
          />
          {minArea !== 0 && (
            <button 
              onClick={() => setMinArea(0)} 
              style={{ 
                background: 'transparent', 
                border: '1px solid var(--border-color)', 
                color: 'var(--text-primary)', 
                padding: '2px 8px', 
                borderRadius: '4px', 
                fontSize: '0.75rem', 
                cursor: 'pointer',
                fontWeight: 600,
                transition: 'all 0.15s'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = 'var(--bg-hover)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent';
              }}
            >
              Auto
            </button>
          )}
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
            <div className="kpi-grid animate-slide-up">
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
            <div className="visualizer-layout animate-slide-up delay-1">
              
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
                  ) : viewMode === 'blend' ? (
                    <div className="blend-viewer" style={{ position: 'relative', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' }}>
                      {/* Base layer: Reference Drawing */}
                      <img 
                        src={`${API_BASE}${result.visualizations.annotated_ref}`} 
                        alt="Reference Base"
                        style={{ display: 'block', width: '100%', height: 'auto', userSelect: 'none' }}
                      />
                      {/* Overlay layer: Comparison Drawing with dynamic opacity */}
                      <img 
                        src={`${API_BASE}${result.visualizations.annotated_cmp}`} 
                        alt="Comparison Overlay"
                        style={{ 
                          position: 'absolute', 
                          top: 0, 
                          left: 0, 
                          width: '100%', 
                          height: 'auto', 
                          opacity: blendOpacity / 100, 
                          userSelect: 'none',
                          mixBlendMode: 'normal'
                        }}
                      />
                    </div>
                  ) : (
                    <img 
                      src={getViewerImage()} 
                      alt="Visualization View" 
                      className="canvas-img"
                    />
                  )}
                </div>

                {viewMode === 'blend' && (
                  <div className="blend-control-bar" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1rem', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)', borderBottomLeftRadius: '8px', borderBottomRightRadius: '8px', justifyContent: 'center' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Ref A (Opacity)</span>
                    <input 
                      type="range" 
                      min="0" 
                      max="100" 
                      value={blendOpacity} 
                      onChange={(e) => setBlendOpacity(parseInt(e.target.value))} 
                      style={{ width: '150px', cursor: 'pointer', accentColor: '#3b82f6' }}
                    />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Comp B ({blendOpacity}%)</span>
                  </div>
                )}
              </div>

              {/* Right Column: AI Summary & Stats Details */}
              <div className="details-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', minHeight: '400px' }}>
                
                {/* Sidebar Tab Selector Buttons */}
                <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', gap: '0.5rem' }}>
                  <button 
                    onClick={() => setSidebarTab('info')}
                    style={{
                      flex: 1,
                      background: sidebarTab === 'info' ? 'var(--bg-hover)' : 'transparent',
                      border: 'none',
                      borderBottom: sidebarTab === 'info' ? '2px solid #3b82f6' : '2px solid transparent',
                      color: sidebarTab === 'info' ? 'var(--text-primary)' : 'var(--text-secondary)',
                      padding: '0.5rem',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.35rem',
                      borderRadius: '4px 4px 0 0',
                      transition: 'all 0.15s'
                    }}
                  >
                    <Sparkles size={14} /> Report Info
                  </button>
                  <button 
                    onClick={() => setSidebarTab('chat')}
                    style={{
                      flex: 1,
                      background: sidebarTab === 'chat' ? 'var(--bg-hover)' : 'transparent',
                      border: 'none',
                      borderBottom: sidebarTab === 'chat' ? '2px solid #3b82f6' : '2px solid transparent',
                      color: sidebarTab === 'chat' ? 'var(--text-primary)' : 'var(--text-secondary)',
                      padding: '0.5rem',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.35rem',
                      borderRadius: '4px 4px 0 0',
                      transition: 'all 0.15s'
                    }}
                  >
                    <MessageSquare size={14} /> AI Assistant
                  </button>
                </div>

                {sidebarTab === 'info' ? (
                  <>
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
                  </>
                ) : (
                  /* Chat Assistant UI Block */
                  <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <HelpCircle size={14} />
                      <span>Ask questions to understand the drawings simply.</span>
                    </div>

                    {/* Scrollable messages container */}
                    <div 
                      style={{ 
                        flexGrow: 1, 
                        maxHeight: '300px', 
                        minHeight: '260px', 
                        overflowY: 'auto', 
                        display: 'flex', 
                        flexDirection: 'column', 
                        gap: '0.75rem', 
                        padding: '0.75rem', 
                        border: '1px solid var(--border-color)', 
                        borderRadius: '6px', 
                        background: 'var(--bg-secondary)',
                        marginBottom: '0.75rem'
                      }}
                    >
                      {chatHistory.length === 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', justifyItems: 'center', alignItems: 'center', margin: 'auto', gap: '0.25rem', opacity: 0.65, textAlign: 'center', padding: '1rem' }}>
                          <MessageSquare size={28} style={{ color: '#3b82f6', marginBottom: '0.25rem' }} />
                          <p style={{ fontSize: '0.8rem', fontWeight: 600 }}>CAD Assistant Ready</p>
                          <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Click a suggestion below or type your question.</p>
                        </div>
                      ) : (
                        chatHistory.map((msg, index) => (
                          <div 
                            key={index} 
                            style={{ 
                              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                              background: msg.role === 'user' ? '#3b82f6' : 'var(--bg-tertiary)',
                              color: msg.role === 'user' ? '#ffffff' : 'var(--text-primary)',
                              border: msg.role === 'user' ? 'none' : '1px solid var(--border-color)',
                              padding: '0.5rem 0.75rem',
                              borderRadius: msg.role === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                              fontSize: '0.8rem',
                              maxWidth: '85%',
                              lineHeight: '1.4',
                              whiteSpace: 'pre-wrap',
                              boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                            }}
                          >
                            {renderMessageContent(msg.content)}
                          </div>
                        ))
                      )}
                      
                      {chatLoading && (
                        <div 
                          style={{ 
                            alignSelf: 'flex-start',
                            background: 'var(--bg-tertiary)',
                            color: 'var(--text-secondary)',
                            border: '1px solid var(--border-color)',
                            padding: '0.5rem 0.75rem',
                            borderRadius: '12px 12px 12px 0',
                            fontSize: '0.8rem',
                            maxWidth: '85%',
                            display: 'flex',
                            gap: '0.35rem',
                            alignItems: 'center'
                          }}
                        >
                          <span className="spinner" style={{ width: '10px', height: '10px', borderWidth: '1.5px', margin: 0 }}></span>
                          Thinking...
                        </div>
                      )}
                      <div ref={chatBottomRef} />
                    </div>

                    {/* Quick Suggestion Pills */}
                    {chatHistory.length === 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.75rem' }}>
                        {[
                          "Explain changes in simple terms",
                          "What is Region 1?",
                          "How do I read this map?",
                          "Is the similarity score high?"
                        ].map((prompt, idx) => (
                          <button
                            key={idx}
                            onClick={() => sendChatMessage(prompt)}
                            style={{
                              background: 'transparent',
                              border: '1px solid var(--border-color)',
                              color: 'var(--text-secondary)',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '0.7rem',
                              cursor: 'pointer',
                              fontWeight: 500,
                              transition: 'all 0.15s'
                            }}
                            onMouseEnter={(e) => { e.target.style.borderColor = '#3b82f6'; e.target.style.color = '#3b82f6'; }}
                            onMouseLeave={(e) => { e.target.style.borderColor = 'var(--border-color)'; e.target.style.color = 'var(--text-secondary)'; }}
                          >
                            {prompt}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Chat Input Field & Send Button */}
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <input 
                        type="text" 
                        placeholder="Ask a question..."
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') sendChatMessage(); }}
                        disabled={chatLoading}
                        style={{ 
                          flexGrow: 1, 
                          background: 'var(--bg-card)', 
                          color: 'var(--text-primary)', 
                          border: '1px solid var(--border-color)', 
                          padding: '0.5rem 0.75rem', 
                          borderRadius: '4px', 
                          fontSize: '0.8rem' 
                        }}
                      />
                      <button 
                        onClick={() => sendChatMessage()}
                        disabled={chatLoading || !chatInput.trim()}
                        style={{ 
                          background: '#3b82f6', 
                          color: '#ffffff', 
                          border: 'none', 
                          padding: '0.5rem 0.85rem', 
                          borderRadius: '4px', 
                          cursor: 'pointer', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center',
                          opacity: (chatLoading || !chatInput.trim()) ? 0.6 : 1
                        }}
                      >
                        <Send size={14} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 3. Regions Table */}
            <div className="regions-table-container animate-slide-up delay-2">
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
