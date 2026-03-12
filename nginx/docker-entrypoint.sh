#!/bin/sh
# OpenResty entrypoint: substitute ${DOMAIN} in all nginx conf templates
# before starting the server.
set -e

DOMAIN="${DOMAIN:-blindstrader.test}"

mkdir -p /etc/nginx/conf.d

# Clear stale conf files so deleted templates don't persist across restarts
rm -f /etc/nginx/conf.d/*.conf

# Process nginx.conf template
envsubst '$DOMAIN' < /etc/nginx/nginx.conf.tpl > /etc/nginx/nginx.conf

# Process each vhost template
for tpl in /nginx-conf-tpl/*.conf; do
    name=$(basename "$tpl")
    envsubst '$DOMAIN' < "$tpl" > "/etc/nginx/conf.d/$name"
done

exec openresty -g 'daemon off;'
