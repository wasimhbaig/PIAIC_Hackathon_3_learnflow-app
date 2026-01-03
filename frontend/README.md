# LearnFlow Frontend

React/Next.js frontend for the LearnFlow AI-powered Python tutoring platform.

## Features

- **Real-time Chat**: WebSocket-based chat with AI Python tutors
- **Code Editor**: Monaco-based Python code editor with live execution
- **Progress Dashboard**: Track mastery scores and learning streaks
- **Responsive Design**: Tailwind CSS for modern, responsive UI

## Tech Stack

- **Next.js 14**: React framework with server-side rendering
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Monaco Editor**: VS Code editor component
- **Axios**: HTTP client for API calls
- **WebSocket**: Real-time communication

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Build for Production

```bash
# Build
npm run build

# Start production server
npm start
```

## Components

### ChatInterface
Real-time chat with AI tutors using WebSocket.

**Features:**
- Auto-scrolling messages
- Agent identification (Triage, Concepts, Debug, etc.)
- Connection status indicator
- Confidence scores

### CodeEditor
Python code editor with execution sandbox.

**Features:**
- Syntax highlighting
- Code execution with output display
- Execution time tracking
- Error handling

### useWebSocket Hook
Custom React hook for WebSocket management.

**Features:**
- Auto-reconnection
- Message queuing
- Connection state management
- Error handling

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://learnflow.local
NEXT_PUBLIC_WS_URL=wss://learnflow.local
```

## Deployment

### Docker

```bash
# Build image
docker build -t learnflow-frontend .

# Run container
docker run -p 3000:3000 learnflow-frontend
```

### Kubernetes

Deploy using the Helm chart in `helm/learnflow/`.

## Development

### Project Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   ├── hooks/          # Custom hooks
│   ├── pages/          # Next.js pages
│   └── services/       # API services
├── public/             # Static assets
├── package.json        # Dependencies
└── tsconfig.json       # TypeScript config
```

### Key Files

- `src/hooks/useWebSocket.ts` - WebSocket connection hook
- `src/components/ChatInterface.tsx` - Chat UI component
- `src/components/CodeEditor.tsx` - Monaco editor component
- `src/pages/index.tsx` - Main dashboard page

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## Future Enhancements

- User authentication UI
- Progress visualization charts
- Exercise library browser
- Quiz interface
- Teacher dashboard
- Mobile responsive improvements
- Offline support
- PWA capabilities
