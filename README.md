Auto refresh your newest IPV6 public IP address to Cloudflare DNS record

Suitable for use with China IPV6 home network.

```bash
docker run -d \
--restart always \
--name cf-ddns \
--env DOMAIN=<your domain> \
--env CLOUDFLARE_API_TOKEN=<your cloudflare api token> \
--env ZONE_ID=<your zone id> \
wh1isper/cf-ddns:latest
```
