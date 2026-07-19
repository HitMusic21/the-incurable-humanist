# Build stage
FROM node:20-alpine AS build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend .
RUN npm run build

# Serve stage
FROM nginx:alpine AS serve
# envsubst ships with nginx:alpine (via `gettext` in the image). Renders the
# nginx config template at container start so BACKEND_URL and PORT can be
# injected from Cloud Run env vars (see frontend/nginx.conf.template).
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf.template /etc/nginx/nginx.conf.template

ENV PORT=8080
# Default backend for local docker-compose (service name `backend` on port 8000
# — matches the compose file's internal port, not the host-mapped 8010).
ENV BACKEND_URL=http://backend:8000

EXPOSE 8080
# Render the template, then exec nginx. Cloud Run sets PORT; we mirror it into
# NGINX_PORT for the template. `-i` on envsubst restricts substitution to the
# vars we name, so any literal `${…}` in the config (nginx uses this syntax
# for its own variables) isn't accidentally clobbered.
CMD ["/bin/sh","-c","export NGINX_PORT=${PORT} && envsubst '$BACKEND_URL $NGINX_PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && exec nginx -g 'daemon off;'"]
