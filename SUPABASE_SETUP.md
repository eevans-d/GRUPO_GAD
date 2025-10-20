# SUPABASE Setup - Automated Guide

Este archivo contiene los pasos para provisionar PostgreSQL en Supabase.

## 🚀 OPCIÓN RÁPIDA: Usar DATABASE_URL con hosting externo

Si ya tienes una conexión PostgreSQL disponible (ej. de Railway anterior), úsala directamente:

```bash
export PATH="/home/eevan/.fly/bin:$PATH"
export FLY_API_TOKEN="[TU_TOKEN]"

# Configura la URL existente
flyctl secrets set \
  DATABASE_URL="postgresql://user:password@host:5432/database" \
  --app grupo-gad
```

## 📝 PASOS MANUALES EN SUPABASE.COM

Si necesitas una nueva instancia PostgreSQL:

1. **Crear Cuenta** → https://supabase.com
   - Sign up con GitHub o email
   
2. **Crear Proyecto**
   - New Project
   - Name: `grupo-gad-db`
   - Region: `us-east-1` (cercano a Dallas)
   - Password: genera fuerte
   
3. **Obtener Connection String**
   - Settings → Database → Connection pooling (recomendado)
   - Copiar URL tipo: `postgresql://postgres:PASS@db.HASH.supabase.co:5432/postgres`

4. **Configurar en Fly.io**
   ```bash
   flyctl secrets set DATABASE_URL="postgresql://..." -a grupo-gad
   ```

5. **Verificar Secret**
   ```bash
   flyctl secrets list -a grupo-gad
   ```

---

## ✅ Una vez configurado DATABASE_URL

Los siguientes comandos habilitarán la base de datos:

```bash
# 1. Editar fly.toml para habilitar release_command
# Descomenta la línea que dice:
# release_command = "alembic upgrade head"

# 2. Commit y push
git add fly.toml
git commit -m "enable: release_command with DATABASE_URL configured"
git push origin master

# 3. Redeploy
flyctl deploy --local-only -a grupo-gad

# 4. Ver logs de migraciones
flyctl logs -a grupo-gad --follow
```

---

**Nota**: Por ahora, el app funciona sin base de datos. Una vez que configures DATABASE_URL y hagas redeploy, las tablas se crearán automáticamente.
