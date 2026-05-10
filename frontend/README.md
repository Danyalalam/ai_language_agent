# Pronunciation Bot Frontend

A modern React frontend for the Pronunciation Bot application that helps users practice and assess their pronunciation in various languages.

## Features

- **Multiple Pronunciation Modes**
  - Reading: Assess pronunciation from prepared scripts
  - Speaking: Evaluate free-form speech on chosen topics
  - Gaming: Practice with tongue twisters

- **Multiple Language Support**
  - German (Germany, Austria, Switzerland)
  - English (US, UK)
  - French
  - Spanish

- **Audio Input Methods**
  - Record directly from microphone
  - Upload audio files
  - Drag and drop support

- **Detailed Assessment Results**
  - Overall pronunciation score
  - Accuracy score with visual progress bar
  - Fluency score
  - Error detection (mispronunciations, omissions, insertions)
  - Visual representation of assessment results

## Project Structure

```
src/
├── components/           # React components
│   ├── ConfigPanel.tsx       # Left sidebar with settings
│   ├── TextInput.tsx         # Text input area
│   ├── AudioRecorder.tsx     # Microphone recording
│   ├── AudioUploader.tsx     # File upload and drag-drop
│   └── AssessmentResult.tsx  # Results display
├── services/
│   └── api.ts            # Backend API communication
├── types/
│   └── index.ts          # TypeScript type definitions
├── styles/               # Component-specific styles
├── App.tsx              # Main application component
├── index.css            # Global styles
└── main.tsx             # Entry point
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm 8+
- Backend API server running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Environment Configuration

By default, the frontend connects to `http://localhost:8000/api` for backend requests. To change this, modify the `API_BASE_URL` in `src/services/api.ts`:

```typescript
const API_BASE_URL = 'http://your-backend-url/api';
```

## API Integration

The frontend communicates with the backend through REST APIs:

- `GET /api/config` - Get available modes and languages
- `POST /api/assess/text` - Assess pronunciation from text
- `POST /api/assess/audio` - Assess pronunciation from audio file
- `GET /api/voices/{language}` - Get available voices for a language

For detailed API documentation, refer to the backend project's README.

## Component Details

### ConfigPanel
Displays pronunciation mode options, language selection, and advanced options. Updates the application state when selections change.

### TextInput
Provides a textarea for entering or editing the text to be assessed. Supports tabs for sample text and custom input.

### AudioRecorder
Records audio directly from the user's microphone with a visual timer. Includes start/stop controls.

### AudioUploader
Allows file upload and drag-drop functionality for audio files. Supports multiple audio formats.

### AssessmentResult
Displays comprehensive assessment results including:
- Pronunciation score (visual circular gauge)
- Accuracy and fluency scores with progress bars
- Detected errors with word-level details
- Audio playback controls

## Technologies Used

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Axios** - HTTP client for API calls
- **Lucide React** - Icon library
- **CSS3** - Styling with flexbox and grid

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

This project is part of the Pronunciation Bot application.

## Contributing

For issues or improvements, please refer to the main project repository.
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
