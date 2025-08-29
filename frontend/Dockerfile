FROM oven/bun:1

WORKDIR /app

# Set NODE_OPTIONS to limit memory usage
ENV NODE_OPTIONS="--max-old-space-size=2048"

COPY package.json bun.lockb ./
RUN bun install

COPY . .

# Expose the port for the development server
EXPOSE 3000

# Add health check to monitor container health
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Run the development server instead of building for production
CMD ["bun", "run", "start"]