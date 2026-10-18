FROM caddy:alpine
COPY config/Caddyfile /etc/caddy/Caddyfile
COPY public /srv/public

