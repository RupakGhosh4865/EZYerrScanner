import { UploadCloud } from 'lucide-react';

export default function FileUpload({ onAnalyze }) {
  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('active');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('active');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('active');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  };

  const handleFile = (file) => {
    onAnalyze(file);
  };

  const fetchSample = async () => {
    try {
      // Create a dummy file from a public URL or local asset if available.
      // Since it's local development, assume backend serves samples or load manually.
      // We'll dispatch a mock file object or ask to select sample_data.
      alert("Sample loading requires backend file path. Please select test_projects.csv manually or copy it.");
    } catch(err) {
      console.error(err);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <label 
        className="dropzone"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <UploadCloud className="dropzone-icon" />
        <h3 style={{ margin: '0 0 10px 0', fontSize: '1.4rem' }}>Drag & Drop your dataset here</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '20px' }}>or click to browse from your computer</p>
        <input 
          type="file" 
          onChange={handleFileChange} 
          style={{ display: 'none' }} 
          accept=".csv,.xlsx,.xls,.json" 
        />
        <button type="button" onClick={() => document.querySelector('input[type="file"]').click()}>
          Select File
        </button>
      </label>
      <div style={{ textAlign: 'center', marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Supports CSV, XLSX, JSON · Max 10MB
      </div>
      <div style={{ textAlign: 'center' }}>
        <button className="sample-link" onClick={fetchSample}>
          Try with sample data (test_projects.csv)
        </button>
      </div>
    </div>
  );
}
