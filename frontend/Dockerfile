# Multi-stage Dockerfile for Next.js 15 (Yarn)
# Stage 1: deps
FROM node:22-alpine AS deps
WORKDIR /app

# Fixes for native deps on Alpine (usually harmless even if unused)
RUN apk add --no-cache libc6-compat

# Install dependencies with good caching
COPY package.json yarn.lock ./
RUN corepack enable \
  && corepack prepare yarn@1.22.22 --activate \
  && yarn install --frozen-lockfile

# Stage 2: builder
FROM node:22-alpine AS builder
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Reuse node_modules from deps layer
COPY --from=deps /app/node_modules ./node_modules

# Copy application source
COPY . .

# IMPORTANT: Your prebuild hook references ../openapi.json.
# This COPY expects the Docker build context to include openapi.json at repo root.
# When building with context set to the repository root, this will succeed and
# allow the prebuild scripts to run (they will find ../openapi.json from /app).
# If your build context is ./frontend, this file is not available and build will fail.
ARG OPENAPI_SPEC_PATH=./docs/openapi.json
COPY ${OPENAPI_SPEC_PATH} /openapi.json

# Build Next.js (will run prebuild hooks defined in package.json)
RUN yarn build

# Stage 3: runner
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

# Copy production artifacts
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/next.config.ts ./next.config.ts

# Drop privileges
USER node

CMD ["yarn", "start", "-p", "3000"]
