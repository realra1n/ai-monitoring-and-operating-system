FROM nginx:alpine
RUN apk add --no-cache curl bash ca-certificates python3 py3-psutil py3-requests py3-yaml \
	&& update-ca-certificates
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY app.js /usr/share/nginx/html/app.js
COPY login.html /usr/share/nginx/html/login.html
COPY login.js /usr/share/nginx/html/login.js
# Proxy /api to backend service name via nginx default upstream override (simple)
RUN sed -i 's#location / {#location /api/ { proxy_pass http://oneservice-backend:8000; }\n    location / {#' /etc/nginx/conf.d/default.conf || true
EXPOSE 80
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
