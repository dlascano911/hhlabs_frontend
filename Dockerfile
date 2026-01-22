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

# Expose the port
EXPOSE 3000

# Use the PORT environment variable
ENV PORT=3000

# Start the server
CMD ["serve", "-s", "dist", "-l", "3000"]
