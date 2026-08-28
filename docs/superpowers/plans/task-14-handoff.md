# Marcá Mi Notebook — pendientes (Task 14: setup + E2E manual)

Repo: `/Users/tomasvazquez/Develop/marca-mi-notebook` (31 commits, backend + frontend + tests completos, final review PASS). Falta solo esto — todo requiere credenciales/acciones humanas.

## 0. Conectar el MCP de Supabase (bloqueado, primero esto)

Ya está agregado en `.mcp.json` (scope proyecto):
```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp?project_ref=xizjjpgkrtnalpfhjcgz&features=docs%2Caccount%2Cdatabase%2Cdebugging%2Cdevelopment%2Cfunctions%2Cbranching"
    }
  }
}
```
Sigue en "not connected" tras varios intentos de `/mcp`. Es un servidor HTTP con OAuth — necesita que el navegador complete el login/autorización y que la sesión de Claude Code se reinicie después. Pasos a reintentar en la nueva conversación:
1. Correr `/mcp` en terminal interactiva (no en la extensión de VSCode si eso no dispara el navegador).
2. Elegir `supabase` → seguir el link de autorización → loguearse en Supabase → aprobar acceso al proyecto `xizjjpgkrtnalpfhjcgz`.
3. Cerrar y volver a abrir Claude Code (reinicio completo, no solo `/clear`).
4. Confirmar con `/mcp` que dice "connected".

Si sigue sin conectar después de esto, hacer el setup de Supabase a mano por la web (supabase.com/dashboard) en vez de por MCP — no es bloqueante para lo demás.

## 1. Crear cuentas y juntar credenciales

- **Supabase** (proyecto `xizjjpgkrtnalpfhjcgz` ya existe): Settings → Database → connection string (`DATABASE_URL`); Settings → API → Project URL (`SUPABASE_URL`) y key `service_role` (`SUPABASE_KEY`); Storage → crear bucket `logos` público.
- **Mercado Pago sandbox**: developers.mercadopago.com.ar → tu app → credenciales de **test** → Access Token (`MERCADOPAGO_ACCESS_TOKEN`). Crear un usuario de prueba comprador. Tarjetas de test: Visa `4509 9535 6623 3704`, cualquier CVV/vencimiento futuro.
- **Resend**: resend.com → API Keys → generar (`RESEND_API_KEY`). Para test no hace falta verificar dominio: `MAIL_FROM=onboarding@resend.dev` ya está seteado en `.env.example`.

## 2. Completar `.env`

`backend/.env` ya existe (copiado de `.env.example`, gitignored) — falta llenar con valores reales:
```
DATABASE_URL=
SUPABASE_URL=
SUPABASE_KEY=
MERCADOPAGO_ACCESS_TOKEN=
RESEND_API_KEY=
ADMIN_EMAIL=
ADMIN_PASSWORD=
WEBHOOK_SECRET=          # ej: openssl rand -hex 32
```
`frontend/.env` también ya existe (copiado de `.env.example`, no necesita cambios para local).

## 3. Levantar local

```bash
# terminal 1
cd backend && uv run uvicorn app:app --reload
# terminal 2
cd frontend && pnpm dev
```
`localhost:5173`. El backend siembra los 10 spots solo al arrancar (`init_db`/`seed_db`).

## 4. Túnel para el webhook de MP

Localhost no es alcanzable por Mercado Pago:
```bash
ngrok http 8000
```
Poner la URL de ngrok en `backend/.env` como `BACKEND_URL=https://xxxx.ngrok-free.app` y reiniciar el backend.

## 5. Checklist E2E manual (Task 14 original)

1. `localhost:5173` → 10 lugares vacíos, termómetro en $0.
2. "Superar" en un spot → nombre, mail, monto, logo → "Ir a pagar".
3. Pagar en el checkout de MP con tarjeta de test + usuario comprador de prueba.
4. Vuelve a `/success` → esperar ~5s → el spot muestra el logo/nombre nuevo.
5. Pujar de nuevo por el mismo spot con monto mayor y otro mail.
6. Verificar mail de "te superaron" al primer bidder (logs en resend.com/emails).
7. `/admin` → login con `ADMIN_EMAIL`/`ADMIN_PASSWORD`.
8. Ver todos los spots + mails de bidders (no visibles en la vista pública).
9. "Cerrar lugar" en un spot → confirmar que ya no acepta pujas.
10. "Rechazar" una puja pagada → confirmar el reembolso en mercadopago.com.ar/activities.

## Pendiente conocido (no bloqueante)

- Tabla de historial de ofertas no se muestra en la UI pública (hook existe, no está enganchado a ningún componente).
- Test de concurrencia real (dos webhooks simultáneos contra Postgres real) queda deferred — el suite actual mockea la DB.
