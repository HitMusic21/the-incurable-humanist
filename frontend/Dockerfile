# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci
COPY frontend .
RUN npm run build

# Serve stage
FROM nginx:alpine AS serve
COPY --from=build /app/frontend/dist /usr/share/nginx/html
# Optional: custom nginx.conf could be copied if routing needs
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
