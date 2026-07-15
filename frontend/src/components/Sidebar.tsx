import React from 'react';
import { MessageCircle, Mic2, Languages } from 'lucide-react';
import '../styles/Sidebar.css';

export type AppView = 'tutor' | 'pronunciation';

interface SidebarProps {
  view: AppView;
  onViewChange: (view: AppView) => void;
}

interface NavItem {
  id: AppView;
  label: string;
  hint: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'tutor',
    label: 'German Tutor',
    hint: 'Live voice conversation',
    icon: <MessageCircle size={20} />,
  },
  {
    id: 'pronunciation',
    label: 'Pronunciation',
    hint: 'Score your speech',
    icon: <Mic2 size={20} />,
  },
];

const Sidebar: React.FC<SidebarProps> = ({ view, onViewChange }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-logo">
          <Languages size={22} />
        </span>
        <div className="sidebar-brand-text">
          <span className="sidebar-title">Sprachcoach</span>
          <span className="sidebar-subtitle">AI Language Agent</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`sidebar-item ${view === item.id ? 'active' : ''}`}
            onClick={() => onViewChange(item.id)}
          >
            <span className="sidebar-item-icon">{item.icon}</span>
            <span className="sidebar-item-text">
              <span className="sidebar-item-label">{item.label}</span>
              <span className="sidebar-item-hint">{item.hint}</span>
            </span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-badge">Powered by Azure VoiceLive</span>
      </div>
    </aside>
  );
};

export default Sidebar;
