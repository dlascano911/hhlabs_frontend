FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Install serve globally to serve static files
RUN npm install -g serve

# Copy serve configuration
COPY serve.json ./

# Expose the port (Cloud Run uses PORT env var)
EXPOSE 8080

# Use the PORT environment variable (default 8080 for Cloud Run)
ENV PORT=8080

# Start the server - use sh to expand PORT variable
CMD ["sh", "-c", "serve -s dist -c serve.json -l ${PORT}"]
