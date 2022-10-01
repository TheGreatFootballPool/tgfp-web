# Great Football Pool
## Notes during massive refactor

### Uses the following
- Install docker
- Make directory somewhere on unix machine
- write this docker compose
```yaml
version: '3.8'

services:
  tgfp-web:
    image: johnofcamas/tgfp-web:latest
    container_name: tgfp-web
    restart: unless-stopped
    command: doppler run --command="gunicorn -b 0.0.0.0:8000 app:app"
    networks:
      my-network:
        aliases:
          - tgfp-web
    environment:
      - DOPPLER_TOKEN=<insert token here>

  nginx:
    image: nginx:latest
    container_name: nginx
    volumes:
      - ./data/certs:/etc/nginx/certs:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    networks:
      - my-network
    depends_on:
      - tgfp-web

networks:
  my-network:

```
- Create nginx.conf file:
```
events { worker_connections 1024; }

http {

    upstream app_servers {    # Create an upstream for the web servers
        server tgfp-web:80;    # the first server
    }

    server {
        listen 80;
        listen [::]:80;

        server_name tgfp.us www.tgfp.us;
        location / {
            proxy_pass http://tgfp-web:8000;
        }
    }
}

```
- Install cloudflares ssl certificates
  - install into `data/certs`
- (see: https://kb.virtubox.net/knowledgebase/cloudflare-ssl-origin-certificates-nginx/)
- open port 80, 443

