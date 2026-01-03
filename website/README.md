# LearnFlow Documentation Site

Docusaurus-based documentation for the LearnFlow AI tutoring platform.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Open http://localhost:3000
```

## Build

```bash
# Build static site
npm run build

# Serve production build
npm run serve
```

## Structure

```
website/
├── docs/              # Documentation markdown files
├── blog/              # Blog posts
├── src/
│   ├── components/    # React components
│   ├── pages/         # Custom pages
│   └── css/           # Custom styles
├── static/            # Static assets
├── docusaurus.config.js  # Site configuration
└── sidebars.js        # Sidebar navigation
```

## Documentation

### Adding New Docs

1. Create markdown file in `docs/`
2. Add frontmatter:
   ```markdown
   ---
   sidebar_position: 1
   ---

   # Title
   ```
3. Update `sidebars.js` if needed

### Blog Posts

Create markdown files in `blog/`:

```markdown
---
title: Post Title
authors: [author]
tags: [tag1, tag2]
---

Content here...
```

## Deployment

### GitHub Pages

```bash
npm run deploy
```

### Docker

```bash
# Build image
docker build -t learnflow-docs .

# Run container
docker run -p 3000:3000 learnflow-docs
```

### Kubernetes

Deploy via Helm chart in `helm/learnflow/`.

## Features

- **Search**: Algolia DocSearch integration
- **Versioning**: Multiple documentation versions
- **i18n**: Internationalization support
- **Dark Mode**: Auto theme switching
- **Code Highlighting**: Prism with Python support
- **MDX**: React components in markdown

## Contributing

1. Fork the repository
2. Create feature branch
3. Add/update documentation
4. Submit pull request

## License

MIT License
