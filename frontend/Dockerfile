# Build stage
FROM node:22-alpine AS build

WORKDIR /app

# Build arguments (needed at build time for Vite)
ARG VITE_STRIPE_PUBLISHABLE_KEY
ENV VITE_STRIPE_PUBLISHABLE_KEY=$VITE_STRIPE_PUBLISHABLE_KEY

ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build app
RUN npm run build

# Production stage - minimal image that holds built files for volume copy
FROM alpine:3.20

# Copy built files to a staging path (NOT the volume mount point)
COPY --from=build /app/dist /build/dist
