# Quick Fix: PostgreSQL via Supabase

## Opción Recomendada: Usar Supabase (Gratuita)

Supabase proporciona PostgreSQL gratuito y fácil de usar:

### Pasos:

1. **Ir a https://supabase.com** y crear cuenta (o usar GitHub login)

2. **Crear nuevo proyecto**:
   - Nombre: `grupo-gad`
   - Password: genera uno fuerte
   - Region: Similar a `dfw` (ej: us-east-1)

3. **Obtener CONNECTION STRING**:
   - Ir a Project Settings → Database
   - Buscar "Connection string"
   - Copiar la URL tipo: `postgresql://postgres:[PASSWORD]@db.[RANDOM].supabase.co:5432/postgres`

4. **Configurar en Fly.io**:
   ```bash
   export FLY_API_TOKEN="[tu token]"
   export PATH="/home/eevan/.fly/bin:$PATH"
   
   flyctl secrets set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[RANDOM].supabase.co:5432/postgres" \
     --app grupo-gad
   ```

5. **Redeploy**:
   ```bash
   cd /home/eevan/ProyectosIA/GRUPO_GAD
   flyctl deploy --local-only --app grupo-gad
   ```

---

## Alternativa: Render.com PostgreSQL

1. Ir a https://render.com
2. Create → PostgreSQL
3. Copiar Internal Database URL
4. Configurar como arriba

---

## Alternativa: Railway PostgreSQL

1. Ir a https://railway.app
2. Create New → Database → PostgreSQL
3. Copiar DATABASE_URL
4. Configurar como arriba

---

**NOTA**: Una vez que el app esté corriendo, ejecutaremos:
```bash
flyctl deploy
```
Esto correrá las migraciones automáticamente.
