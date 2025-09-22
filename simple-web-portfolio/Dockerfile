
# Multi-stage build for optimization
FROM nginx:alpine AS base

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup -g 1001 -S nginxuser && \
    adduser -S nginxuser -u 1001

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy website files
COPY index.html /usr/share/nginx/html/

# Set proper permissions
RUN chown -R nginxuser:nginxuser /usr/share/nginx/html /var/cache/nginx /var/run

# Switch to non-root user
USER nginxuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]