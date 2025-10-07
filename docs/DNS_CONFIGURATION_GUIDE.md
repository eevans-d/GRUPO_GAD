# Configuración DNS para GRUPO_GAD

Este documento detalla la configuración DNS necesaria para el despliegue en producción de la aplicación GRUPO_GAD. Forma parte de la fase 5.2 del roadmap de producción.

## Registros DNS Requeridos

La siguiente tabla muestra los registros DNS que deben configurarse para el correcto funcionamiento del sistema:

| Tipo | Nombre | Valor | TTL | Propósito |
|------|--------|-------|-----|-----------|
| A | api.grupogad.com | IP_DEL_SERVIDOR | 300 | API principal |
| A | grupogad.com | IP_DEL_SERVIDOR | 300 | Sitio web principal |
| A | admin.grupogad.com | IP_DEL_SERVIDOR | 300 | Panel de administración |
| A | metrics.grupogad.com | IP_DEL_SERVIDOR | 3600 | Endpoint Prometheus |
| CNAME | www.grupogad.com | grupogad.com | 3600 | Redirección www |
| TXT | _dmarc.grupogad.com | "v=DMARC1; p=reject; rua=mailto:admin@grupogad.com" | 3600 | Políticas DMARC |
| TXT | grupogad.com | "v=spf1 include:_spf.google.com ~all" | 3600 | SPF para correo |
| MX | grupogad.com | 10 mail.grupogad.com | 3600 | Servidor de correo |
| CAA | grupogad.com | 0 issue "letsencrypt.org" | 3600 | Autoridad certificadora |

> Notas: 
> - Reemplazar `IP_DEL_SERVIDOR` con la dirección IP pública del servidor de producción.
> - Los TTL (Time To Live) están en segundos. Para pruebas iniciales, usar valores bajos como 300 (5 minutos).
> - En producción, considerar aumentar los TTL para reducir consultas DNS.

## Proveedor de DNS

Se recomienda utilizar un proveedor de DNS que ofrezca:

1. Panel de control intuitivo
2. Soporte para todos los tipos de registros requeridos
3. API para automatización
4. DDoS protection
5. DNSSEC (opcional pero recomendado)

Opciones recomendadas:
- Cloudflare
- Amazon Route 53
- Google Cloud DNS

## Configuración DNSSEC (opcional)

Para una capa adicional de seguridad, se recomienda habilitar DNSSEC:

1. Generar llaves DNSSEC en el proveedor de DNS
2. Publicar registros DS en el registrador del dominio
3. Verificar la configuración con herramientas como [DNSViz](https://dnsviz.net/)

## Consideraciones Especiales para Caddy

Como usamos Caddy como servidor web y proxy inverso, este obtendrá automáticamente certificados SSL de Let's Encrypt. Para garantizar que esto funcione correctamente:

1. Asegurarse que los puertos 80 y 443 estén abiertos en el firewall
2. Verificar que los registros A/CNAME apunten al servidor correcto
3. Confirmar que no existan registros CAA que bloqueen Let's Encrypt

## Procedimiento de Verificación

Después de configurar los registros DNS:

1. Esperar al menos el tiempo del TTL para que los cambios se propaguen
2. Verificar la resolución de nombres:
   ```bash
   dig +short api.grupogad.com
   dig +short grupogad.com
   ```
3. Verificar la configuración DNS completa:
   ```bash
   dig grupogad.com ANY
   ```
4. Comprobar la validación DNSSEC (si está habilitado):
   ```bash
   dig grupogad.com +dnssec
   ```

## Monitoreo DNS

Para monitorear la disponibilidad y rendimiento DNS:

1. Configurar alertas de expiración de dominio
2. Implementar chequeos periódicos de resolución DNS
3. Usar servicios como UptimeRobot o StatusCake para monitoreo externo

## Plan de Contingencia

En caso de problemas DNS:

1. Mantener configuración DNS secundaria documentada
2. Considerar un proveedor DNS secundario
3. Documentar contactos de soporte del proveedor DNS
4. Tener acceso a las credenciales del registrador y proveedor DNS

## Automatización

Para entornos con múltiples dominios o subdominio, considerar automatizar la gestión DNS:

1. Usar Terraform para gestionar registros DNS como código
2. Implementar scripts para verificación periódica de configuración
3. Documentar cualquier modificación manual en un registro de cambios

---

## Referencias

- [RFC 1034](https://tools.ietf.org/html/rfc1034) - Conceptos y configuración DNS
- [RFC 4033](https://tools.ietf.org/html/rfc4033) - Extensiones de Seguridad DNS (DNSSEC)
- [RFC 7719](https://tools.ietf.org/html/rfc7719) - Terminología DNS
- [Caddy Documentation - Automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [Let's Encrypt - CAA](https://letsencrypt.org/docs/caa/)