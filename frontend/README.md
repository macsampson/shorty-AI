# AI Content Generator Frontend

This is a simple React frontend for the AI Content Generator application. It allows you to generate AI content by providing text prompts.

## Features

- Text input for prompting the AI to generate content
- View previously generated content
- Display generated videos, images, and scripts

## Getting Started

### Running with Docker

The easiest way to run the application is using Docker Compose:

```bash
docker-compose up -d
```

This will start the frontend service along with the API and other required services. The frontend will be available at http://localhost:3000.

### Running Locally for Development

If you want to run the frontend locally for development:

1. Install dependencies:

```bash
cd frontend
npm install
# or
yarn install
# or
bun install
```

2. Start the development server:

```bash
npm start
# or
yarn start
# or
bun start
```

The frontend will be available at http://localhost:3000.

## Usage

1. Enter a prompt in the text area (e.g., "Create a short video about space exploration")
2. Click the "Generate Content" button
3. Wait for the content to be generated (this may take several minutes)
4. Once complete, your content will appear in the "Previous Generations" list
5. Click on a folder to view the generated content

## API Integration

The frontend communicates with the API at http://localhost:8000. The main endpoints used are:

- `/generate_video` - Generates a video based on a text prompt
- `/list_generated_content` - Lists all previously generated content
- `/get_generated_content/{folder_name}` - Gets the content for a specific folder

## Technologies Used

- React
- TypeScript
- Axios for API requests
- Docker for containerization
