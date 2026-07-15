import { useState } from 'react';
import Sidebar, { type AppView } from './components/Sidebar';
import GermanVoiceChat from './components/GermanVoiceChat';
import PronunciationView from './components/PronunciationView';
import './App.css';

function App() {
  const [view, setView] = useState<AppView>('tutor');

  return (
    <div className="app">
      <Sidebar view={view} onViewChange={setView} />
      <main className="main-content">
        <div className="content-wrapper">
          {view === 'tutor' ? <GermanVoiceChat /> : <PronunciationView />}
        </div>
      </main>
    </div>
  );
}

export default App;
