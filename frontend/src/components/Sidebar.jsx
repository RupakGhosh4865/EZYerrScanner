import { Home, Search, History, CreditCard, Settings, LogOut, Shield, X } from 'lucide-react';

export default function Sidebar({ isOpen, onClose }) {
  const menuItems = [
    { icon: <Home size={20} />, label: 'Home', active: true },
    { icon: <Search size={20} />, label: 'New Scan' },
    { icon: <History size={20} />, label: 'Previous Scans' },
    { icon: <CreditCard size={20} />, label: 'Pricing' },
    { icon: <Settings size={20} />, label: 'Settings' },
  ];

  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <button 
        className="mobile-close-btn" 
        onClick={onClose}
        style={{ 
          position: 'absolute', top: '1.5rem', right: '1.5rem', 
          background: 'transparent', border: 'none', color: 'var(--text-grey)',
          display: 'none' // Hidden by default, shown in media query
        }}
      >
        <X size={24} />
      </button>

      <div className="sidebar-logo">
        <div className="logo-box">
          <Shield size={24} color="var(--neon-blue)" />
        </div>
        <div className="logo-text">
          <span className="brand-name">EZYerrScanner</span>
          <span className="brand-version">SYSTEM.V1</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item, i) => (
          <div key={i} className={`nav-item ${item.active ? 'active' : ''}`}>
            {item.icon}
            <span className="nav-label">{item.label}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="credits-card">
          <div className="credits-header">
            <span className="credits-icon">⚡</span>
            <span className="credits-label">Credits</span>
            <span className="credits-value">Unlimited</span>
          </div>
        </div>
        
        <div className="user-card">
          <div className="user-avatar">U</div>
          <div className="user-info">
            <span className="user-name">User</span>
            <span className="user-plan">PRO PLAN</span>
          </div>
        </div>

        <div className="logout-btn">
          <LogOut size={18} />
          <span>LOGOUT</span>
        </div>
      </div>
    </div>
  );
}
