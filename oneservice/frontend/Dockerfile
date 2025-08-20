FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY app.js /usr/share/nginx/html/app.js
# Proxy /api to backend service name via nginx default upstream override (simple)
RUN sed -i 's#location / {#location /api/ { proxy_pass http://oneservice-backend:8000/; }\n    location / {#' /etc/nginx/conf.d/default.conf || true
EXPOSE 80
