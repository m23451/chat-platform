# Frontend: static files served by NGINX, running as a non-root user on port 8080.
FROM nginxinc/nginx-unprivileged:1.27-alpine

# Install the latest Alpine security fixes
USER root
RUN apk upgrade --no-cache
USER 101
ARG APP_VERSION=dev
ARG GIT_COMMIT=unknown
LABEL org.opencontainers.image.title="chat-frontend" \
      org.opencontainers.image.version=$APP_VERSION \
      org.opencontainers.image.revision=$GIT_COMMIT

# Where NGINX forwards /api and /api/message-ws (service name:port)
ENV API_UPSTREAM=chat-api:8000

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY public/ /usr/share/nginx/html/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
