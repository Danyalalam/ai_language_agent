# Pronunciation Bot Frontend - Copilot Instructions

## Project Overview

This is a React TypeScript frontend for the Pronunciation Bot application. It provides a user interface for pronunciation assessment with multiple modes (reading, speaking, gaming) and language support.

## Architecture

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: React hooks (useState)
- **Styling**: CSS modules and component-scoped CSS
- **API Communication**: Axios
- **Icons**: Lucide React

## File Structure

```
src/
├── components/           # React components
│   ├── ConfigPanel.tsx       # Configuration sidebar
│   ├── TextInput.tsx         # Text input component
│   ├── AudioRecorder.tsx     # Microphone recording
│   ├── AudioUploader.tsx     # File upload and drag-drop
│   └── AssessmentResult.tsx  # Results visualization
├── services/
│   └── api.ts                # API service layer
├── types/
│   └── index.ts              # TypeScript interfaces
├── styles/                   # Component styles
│   ├── ConfigPanel.css
│   ├── TextInput.css
│   ├── AudioRecorder.css
│   ├── AudioUploader.css
│   └── AssessmentResult.css
├── App.tsx                   # Main application
├── index.css                 # Global styles
└── main.tsx                  # React entry point
```

## Key Types

- `PronunciationMode`: 'reading' | 'speaking' | 'gaming'
- `Language`: Supported languages for assessment
- `AssessmentResult`: Contains scores, errors, and assessment details
- `Config`: Available modes and languages from backend

## Backend Integration

The frontend expects a backend API at `http://localhost:8000/api` with these endpoints:

- `GET /api/config` - Configuration with modes and languages
- `POST /api/assess/text` - Assess from text
- `POST /api/assess/audio` - Assess from audio file
- `GET /api/voices/{language}` - Available voices

To change the backend URL, modify `API_BASE_URL` in `src/services/api.ts`.

## Development Guidelines

1. **Component Structure**: Each component is self-contained with its own CSS file
2. **Type Safety**: Always use TypeScript interfaces from `src/types/index.ts`
3. **API Communication**: Use the `api` service from `src/services/api.ts`
4. **Error Handling**: Components should handle loading and error states
5. **Styling**: Use component-scoped CSS for maintainability

## Common Tasks

### Adding a New Component

1. Create component file in `src/components/ComponentName.tsx`
2. Create corresponding CSS file in `src/styles/ComponentName.css`
3. Add TypeScript interfaces if needed in `src/types/index.ts`
4. Import and use in App.tsx

### Modifying API Endpoints

Edit `src/services/api.ts` and update the corresponding function.

### Changing Styling

Update the component's CSS file in `src/styles/` directory.

### Updating Types

Modify `src/types/index.ts` to add or change interfaces.

## Running the Project

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Testing the Frontend

1. Ensure backend is running on `http://localhost:8000`
2. Start frontend with `npm run dev`
3. Open `http://localhost:5173` in browser
4. Test each mode and language selection
5. Test audio recording and file upload
6. Verify assessment results display

## Performance Considerations

- Components use React.memo for optimization where needed
- CSS is scoped to components to avoid conflicts
- API requests are debounced in audio uploader
- Large results are virtualized if needed

## Debugging Tips

1. Check browser console for API errors
2. Use React DevTools for component inspection
3. Verify backend is running and accessible
4. Check network tab for API request/response
5. Enable verbose logging in api.ts for debugging

## Future Enhancements

- Dark mode support
- Accessibility improvements (ARIA labels)
- Performance optimization with virtualization
- Multi-language UI support
- Advanced audio visualization
- User profile and history

## Notes

- The application uses browser's MediaRecorder API for audio recording
- Audio files are sent as FormData to support multipart/form-data
- Error details are highlighted in the assessment results
- Scores are visualized with circular gauge and progress bars
