"""
Production-Ready Dockerfile Generator

Generates optimized, production-ready Dockerfiles for all major frameworks:
- Multi-stage builds for smaller images
- Security best practices (non-root user, minimal base images)
- Proper caching layers
- Health checks
- Framework-specific optimizations
"""

import os
from typing import Optional


def generate_dockerfile(app_path: str, analysis: dict = None, 
                       python_version: str = None,
                       node_version: str = None) -> str:
    """
    Generate optimized Dockerfile based on framework analysis.
    
    Args:
        app_path: Path to application
        analysis: Analysis result from analyzer (if not provided, will analyze)
        python_version: Python version for Python apps (auto-detected if not provided)
        node_version: Node version for Node.js apps (auto-detected if not provided)
        
    Returns:
        Dockerfile content as string
    """
    
    if analysis is None:
        from .analyzer import analyze_application
        analysis = analyze_application(app_path)
    
    # Use detected language version from analysis, or provided version, or fallback to defaults
    detected_version = analysis.get('language_version')
    if not python_version and analysis.get('app_type') == 'python':
        python_version = detected_version or "3.11"
    if not node_version and analysis.get('app_type') == 'node':
        node_version = detected_version or "20"
    
    # Ensure we have version values
    python_version = python_version or "3.11"
    node_version = node_version or "20"
    
    framework = (analysis.get('framework') or '').lower()
    app_type = (analysis.get('app_type') or '').lower()
    
    # Route to specific generator
    if framework == 'django':
        return _generate_django_dockerfile(app_path, analysis, python_version)
    elif framework == 'flask':
        return _generate_flask_dockerfile(app_path, analysis, python_version)
    elif framework == 'fastapi':
        return _generate_fastapi_dockerfile(app_path, analysis, python_version)
    elif framework == 'nextjs':
        return _generate_nextjs_dockerfile(app_path, analysis, node_version)
    elif framework == 'react':
        return _generate_react_dockerfile(app_path, analysis, node_version)
    elif framework == 'vue':
        return _generate_vue_dockerfile(app_path, analysis, node_version)
    elif framework == 'vite':
        return _generate_vite_dockerfile(app_path, analysis, node_version)
    elif framework == 'angular':
        return _generate_angular_dockerfile(app_path, analysis, node_version)
    elif framework == 'nestjs':
        return _generate_nestjs_dockerfile(app_path, analysis, node_version)
    elif framework == 'express':
        return _generate_express_dockerfile(app_path, analysis, node_version)
    elif framework in ['spring-boot', 'maven']:
        return _generate_springboot_dockerfile(app_path, analysis)
    elif framework == 'go' or framework in ['gin', 'echo', 'fiber']:
        return _generate_go_dockerfile(app_path, analysis)
    elif framework == 'rails':
        return _generate_rails_dockerfile(app_path, analysis)
    elif framework == 'laravel':
        return _generate_laravel_dockerfile(app_path, analysis)
    elif framework == 'aspnetcore' or app_type == 'dotnet':
        return _generate_dotnet_dockerfile(app_path, analysis)
    elif framework == 'static':
        return _generate_static_dockerfile(app_path, analysis)
    elif app_type == 'python':
        return _generate_generic_python_dockerfile(app_path, analysis, python_version)
    elif app_type == 'node':
        return _generate_generic_node_dockerfile(app_path, analysis, node_version)
    else:
        return _generate_generic_dockerfile(app_path, analysis)


def _generate_django_dockerfile(app_path: str, analysis: dict, python_version: str) -> str:
    """Generate optimized Dockerfile for Django applications."""
    return f"""# Multi-stage build for Django
FROM python:{python_version}-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:{python_version}-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/* \\
    && useradd -m -u 1000 appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set PATH for user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE {analysis.get('port', 8000)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:{analysis.get('port', 8000)}/health', timeout=2)" || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:{analysis.get('port', 8000)}", "--workers", "4", "--timeout", "120", "config.wsgi:application"]
"""


def _generate_fastapi_dockerfile(app_path: str, analysis: dict, python_version: str) -> str:
    """Generate optimized Dockerfile for FastAPI applications."""
    entry_point = analysis.get('entry_point', 'main.py').replace('.py', '')
    
    return f"""# Multi-stage build for FastAPI
FROM python:{python_version}-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:{python_version}-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set PATH for user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Expose port
EXPOSE {analysis.get('port', 8000)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:{analysis.get('port', 8000)}/health', timeout=2)" || exit 1

# Run with uvicorn
CMD ["uvicorn", "{entry_point}:app", "--host", "0.0.0.0", "--port", "{analysis.get('port', 8000)}", "--workers", "4"]
"""


def _generate_flask_dockerfile(app_path: str, analysis: dict, python_version: str) -> str:
    """Generate optimized Dockerfile for Flask applications."""
    return f"""# Multi-stage build for Flask
FROM python:{python_version}-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:{python_version}-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set PATH and Flask environment
ENV PATH=/home/appuser/.local/bin:$PATH \\
    FLASK_APP=app.py \\
    FLASK_ENV=production

# Switch to non-root user
USER appuser

# Expose port
EXPOSE {analysis.get('port', 5000)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:{analysis.get('port', 5000)}/health', timeout=2)" || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:{analysis.get('port', 5000)}", "--workers", "4", "app:app"]
"""


def _generate_nextjs_dockerfile(app_path: str, analysis: dict, node_version: str) -> str:
    """Generate optimized Dockerfile for Next.js applications."""
    return f"""# Multi-stage build for Next.js
FROM node:{node_version}-alpine AS deps

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./
RUN \\
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \\
  elif [ -f package-lock.json ]; then npm ci; \\
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \\
  else echo "Lockfile not found." && exit 1; \\
  fi

# Builder stage
FROM node:{node_version}-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

RUN \\
  if [ -f yarn.lock ]; then yarn build; \\
  elif [ -f package-lock.json ]; then npm run build; \\
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm run build; \\
  else npm run build; \\
  fi

# Production stage
FROM node:{node_version}-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE {analysis.get('port', 3000)}

ENV PORT={analysis.get('port', 3000)}
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:{analysis.get('port', 3000)}', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

CMD ["node", "server.js"]
"""


def _generate_react_dockerfile(app_path: str, analysis: dict, node_version: str) -> str:
    """Generate optimized Dockerfile for React applications."""
    return f"""# Multi-stage build for React
FROM node:{node_version}-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies - use npm ci if package-lock.json exists, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci --silent; else npm install --silent; fi

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy custom nginx config if exists
COPY nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || echo "server {{ listen 80; root /usr/share/nginx/html; index index.html; location / {{ try_files \\$uri \\$uri/ /index.html; }} }}" > /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s \\
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
"""


def _generate_vue_dockerfile(app_path: str, analysis: dict, node_version: str) -> str:
    """Generate optimized Dockerfile for Vue applications."""
    return f"""# Multi-stage build for Vue
FROM node:{node_version}-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies - use npm ci if package-lock.json exists, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci --silent; else npm install --silent; fi

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy custom nginx config if exists
COPY nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || echo "server {{ listen 80; root /usr/share/nginx/html; index index.html; location / {{ try_files \\$uri \\$uri/ /index.html; }} }}" > /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s \\
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
"""


def _generate_vite_dockerfile(app_path: str, analysis: dict, node_version: str) -> str:
    """Generate optimized Dockerfile for Vite applications."""
    detected_port = analysis.get('port', 5173)
    
    return f"""FROM node:{node_version}-alpine

WORKDIR /app

RUN addgroup -g 1001 -S nodejs && adduser -S nodeuser -u 1001

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for Vite)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi && npm cache clean --force

# Copy source code
COPY --chown=nodeuser:nodejs . .

USER nodeuser

# Expose the Vite development server port
EXPOSE {detected_port}

# Start Vite development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "{detected_port}"]
"""


def _generate_nestjs_dockerfile(app_path: str, analysis: dict, node_version: str) -> str:
    """Generate optimized Dockerfile for NestJS applications."""
    return f"""# Multi-stage build for NestJS
FROM node:{node_version}-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies - use npm ci if package-lock.json exists, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:{node_version}-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nestjs -u 1001

# Copy package files
COPY package*.json ./

# Install production dependencies only
# Use npm ci if package-lock.json exists, otherwise use npm install
RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --production; fi && npm cache clean --force

# Copy built application from builder
COPY --from=builder --chown=nestjs:nodejs /app/dist ./dist

USER nestjs

# Expose port
EXPOSE {analysis.get('port', 3000)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:{analysis.get('port', 3000)}/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Start application
CMD ["node", "dist/main.js"]
"""


def _generate_express_dockerfile(app_path: str, analysis: dict, node_version: str) -> str:
    """Generate optimized Dockerfile for Express applications."""
    entry_point = analysis.get('entry_point', 'index.js')
    
    return f"""# Multi-stage build for Express
FROM node:{node_version}-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies - use npm ci if package-lock.json exists, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source code
COPY . .

# Production stage
FROM node:{node_version}-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S expressuser -u 1001

# Copy package files
COPY package*.json ./

# Install production dependencies only - use npm ci if package-lock.json exists, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci --only=production && npm cache clean --force; else npm install --production && npm cache clean --force; fi

# Copy application code
COPY --chown=expressuser:nodejs . .

USER expressuser

# Expose port
EXPOSE {analysis.get('port', 3000)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:{analysis.get('port', 3000)}/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Start application
CMD ["node", "{analysis.get('entry_point', 'index.js')}"]
"""


def _generate_go_dockerfile(app_path: str, analysis: dict) -> str:
    """Generate optimized Dockerfile for Go applications."""
    return f"""# Multi-stage build for Go
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Production stage - use distroless for minimal image
FROM gcr.io/distroless/static-debian11

WORKDIR /

# Copy binary from builder
COPY --from=builder /app/main .

# Expose port
EXPOSE {analysis.get('port', 8080)}

# Run as non-root user
USER nonroot:nonroot

# Start application
CMD ["/main"]
"""


def _generate_springboot_dockerfile(app_path: str, analysis: dict) -> str:
    """Generate optimized Dockerfile for Spring Boot applications."""
    return f"""# Multi-stage build for Spring Boot
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /app

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source and build
COPY src ./src
RUN mvn clean package -DskipTests

# Production stage
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -S spring && adduser -S spring -G spring

# Copy JAR from builder
COPY --from=builder --chown=spring:spring /app/target/*.jar app.jar

USER spring:spring

# Expose port
EXPOSE {analysis.get('port', 8080)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\
    CMD wget --quiet --tries=1 --spider http://localhost:{analysis.get('port', 8080)}/actuator/health || exit 1

# JVM options for containers
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"

# Start application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
"""


def _generate_rails_dockerfile(app_path: str, analysis: dict) -> str:
    """Generate optimized Dockerfile for Ruby on Rails applications."""
    return f"""# Multi-stage build for Rails
FROM ruby:3.2-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache build-base postgresql-dev nodejs yarn

# Copy Gemfile
COPY Gemfile Gemfile.lock ./

# Install gems
RUN bundle install --jobs 4 --retry 3

# Production stage
FROM ruby:3.2-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache postgresql-client nodejs yarn tzdata

# Create non-root user
RUN adduser -D -u 1000 rails

# Copy gems from builder
COPY --from=builder /usr/local/bundle /usr/local/bundle

# Copy application code
COPY --chown=rails:rails . .

# Precompile assets
RUN SECRET_KEY_BASE=dummy bundle exec rails assets:precompile || true

USER rails

# Expose port
EXPOSE {analysis.get('port', 3000)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD wget --quiet --tries=1 --spider http://localhost:{analysis.get('port', 3000)}/health || exit 1

# Start Rails server
CMD ["bundle", "exec", "rails", "server", "-b", "0.0.0.0"]
"""


def _generate_laravel_dockerfile(app_path: str, analysis: dict) -> str:
    """Generate optimized Dockerfile for Laravel applications."""
    return f"""# Multi-stage build for Laravel
FROM php:8.2-fpm-alpine AS builder

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \\
    libpng-dev \\
    libzip-dev \\
    zip \\
    unzip \\
    && docker-php-ext-install pdo_mysql gd zip

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy composer files
COPY composer.json composer.lock ./

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Production stage
FROM php:8.2-fpm-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache \\
    nginx \\
    supervisor \\
    libpng \\
    libzip \\
    && docker-php-ext-install pdo_mysql gd zip

# Create non-root user
RUN adduser -D -u 1000 laravel

# Copy vendor from builder
COPY --from=builder /app/vendor ./vendor

# Copy application code
COPY --chown=laravel:laravel . .

# Configure nginx and PHP-FPM
COPY docker/nginx.conf /etc/nginx/http.d/default.conf
COPY docker/supervisord.conf /etc/supervisord.conf

# Optimize Laravel
RUN php artisan config:cache && \\
    php artisan route:cache && \\
    php artisan view:cache || true

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s \\
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Start services with supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
"""


def _generate_dotnet_dockerfile(app_path: str, analysis: dict) -> str:
    """Generate optimized Dockerfile for .NET applications."""
    return f"""# Multi-stage build for .NET
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS builder

WORKDIR /app

# Copy csproj and restore dependencies
COPY *.csproj ./
RUN dotnet restore

# Copy source and build
COPY . ./
RUN dotnet publish -c Release -o out

# Production stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 dotnetuser

# Copy built application from builder
COPY --from=builder --chown=dotnetuser:dotnetuser /app/out .

USER dotnetuser

# Expose port
EXPOSE {analysis.get('port', 5000)}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:{analysis.get('port', 5000)}/health || exit 1

# Start application
ENTRYPOINT ["dotnet", "app.dll"]
"""


def _generate_static_dockerfile(app_path: str, analysis: dict) -> str:
    """Generate Dockerfile for static sites."""
    return """# Static site with nginx
FROM nginx:alpine

# Copy static files
COPY . /usr/share/nginx/html

# Copy custom nginx config if exists
COPY nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || true

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s \\
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
"""


def _generate_generic_python_dockerfile(app_path: str, analysis: dict, python_version: str) -> str:
    """Generate generic Python Dockerfile."""
    return f"""FROM python:{python_version}-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/* \\
    && useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE {analysis.get('port', 8000)}

CMD ["python", "{analysis.get('entry_point', 'main.py')}"]
"""


def _generate_generic_node_dockerfile(app_path: str, analysis: dict, node_version: str) -> str:
    """Generate generic Node.js Dockerfile."""
    return f"""FROM node:{node_version}-alpine

WORKDIR /app

RUN addgroup -g 1001 -S nodejs && adduser -S nodeuser -u 1001

COPY package*.json ./
# Use npm ci if package-lock.json exists, otherwise use npm install
RUN if [ -f package-lock.json ]; then npm ci --only=production; else npm install --production; fi && npm cache clean --force

COPY --chown=nodeuser:nodejs . .

USER nodeuser

EXPOSE {analysis.get('port', 3000)}

CMD ["node", "{analysis.get('entry_point', 'index.js')}"]
"""


def _generate_generic_dockerfile(app_path: str, analysis: dict) -> str:
    """Generate generic Dockerfile as fallback."""
    return """FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

CMD ["echo", "Please configure the start command for your application"]
"""