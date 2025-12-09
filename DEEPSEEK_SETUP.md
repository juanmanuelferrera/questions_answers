# 🚀 DeepSeek Integration Setup Guide

## 📊 Cost Comparison

| Model | Cost/Query | Cost/Month (1k queries/day) | Savings |
|-------|-----------|----------------------------|---------|
| GPT-4o (current) | $0.012 | $360 | Baseline |
| GPT-4o-mini | $0.005 | $150 | 58% |
| **DeepSeek Chat** | **$0.0013** | **$39** | **89%** 🎉 |

---

## 🎁 Free Tier

✅ **5,000,000 tokens gratis** al crear cuenta
- Valor: ~$8.40
- Equivalente: ~1,450 queries
- Validez: 30 días
- **Perfecto para testing!**

---

## 🔑 Cómo Obtener tu API Key de DeepSeek

### Paso 1: Crear Cuenta (2 minutos)

1. **Ve a:** https://platform.deepseek.com
2. **Click en "Sign Up"**
3. **Opciones de registro:**
   - Email + Password
   - GitHub OAuth (recomendado - más rápido)
   - Google OAuth

### Paso 2: Verificar Email

1. Revisa tu inbox
2. Click en link de verificación
3. Confirma tu cuenta

### Paso 3: Obtener API Key (1 minuto)

1. **Login en:** https://platform.deepseek.com
2. **Click en tu perfil** (arriba a la derecha)
3. **Navega a:** "API Keys" en el menú lateral
4. **Click en:** "Create API Key"
5. **Copia la key** (solo se muestra una vez!)

**⚠️ IMPORTANTE:** Guarda tu API key inmediatamente, no podrás verla después.

### Paso 4: Configurar en tu Proyecto

```bash
# 1. Edita wrangler.synthesis.toml
nano wrangler.synthesis.toml

# 2. Reemplaza YOUR_DEEPSEEK_KEY_HERE con tu key real
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxx"

# 3. Guarda el archivo (Ctrl+X, Y, Enter)
```

---

## 🚀 Deploy del Worker

```bash
# Deploy synthesis worker con DeepSeek
npx wrangler deploy --config wrangler.synthesis.toml

# Verificar que está corriendo
curl -X POST https://vedabase-synthesis.YOUR_SUBDOMAIN.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Krishna consciousness?",
    "sources": [...],
    "wordLimit": 300
  }'
```

---

## 📈 Monitoreo de Uso y Costos

### Ver tu Balance en DeepSeek

1. **Login:** https://platform.deepseek.com
2. **Click en:** "Billing" en el menú
3. **Ver:**
   - Granted Balance (5M tokens gratis)
   - Topped-up Balance (dinero que agregaste)
   - Usage (consumo actual)

### Calcular Costo por Query

**Tu configuración actual:**
- Input promedio: ~3,000 tokens
- Output promedio: ~450 tokens

**Costo:**
```
Input:  3,000 tokens × $0.27 / 1M = $0.00081
Output: 450 tokens × $1.10 / 1M = $0.000495
Total:  $0.0013 por query
```

**Con 5M tokens gratis:**
```
5,000,000 tokens ÷ 3,450 tokens/query = ~1,450 queries gratis
```

---

## ✅ Testing Plan

### Fase 1: Validación (Días 1-2)

Usa tus 5M tokens gratis para:

```bash
# Test 1: Query simple
"What is dharma?"

# Test 2: Query compleja
"How do different Vaishnava acharyas interpret the concept of prema?"

# Test 3: Query con múltiples fuentes
"Explain the relationship between jiva and Brahman"
```

**Compara lado a lado:**
- ✓ Calidad de respuesta vs GPT-4o
- ✓ Tiempo de respuesta (latencia)
- ✓ Precisión en citas
- ✓ Coherencia en síntesis

### Fase 2: Decisión (Día 3)

**Si calidad es ≥95% de GPT-4o:**
✅ Continúa con DeepSeek
✅ Agrega $20-50 a tu cuenta
✅ Ahorra 89% en costos

**Si calidad es <95%:**
⚠️ Evalúa alternativas:
- GPT-4o-mini (58% ahorro, mejor calidad)
- Cloudflare Workers AI (gratis, menor calidad)
- Híbrido (DeepSeek simple + GPT-4o complejo)

---

## 🔄 Arquitectura Implementada

```typescript
// synthesis-worker.ts

┌─────────────────────────────────────┐
│   Query recibida del frontend       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   TRY: DeepSeek Chat API            │
│   - 89% más barato                  │
│   - Calidad competitiva             │
│   - ~200ms latencia                 │
└──────────────┬──────────────────────┘
               │
               │ ✓ Success
               ▼
┌─────────────────────────────────────┐
│   Return synthesis + metadata       │
│   - model: "deepseek-chat"          │
│   - cost_savings: "89% vs GPT-4o"   │
└─────────────────────────────────────┘

               │ ✗ Error
               ▼
┌─────────────────────────────────────┐
│   CATCH: Fallback to GPT-4o         │
│   - Garantía de disponibilidad      │
│   - 100% uptime                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Return synthesis + metadata       │
│   - model: "gpt-4o"                 │
│   - cost_savings: "0%"              │
└─────────────────────────────────────┘
```

---

## 🛡️ Seguridad

### API Keys Protegidas

✅ **Keys guardadas en Cloudflare Workers**
- No expuestas en frontend
- No en código fuente
- Solo en variables de entorno

✅ **Rate Limiting**
- Protección contra abuso
- Por IP del cliente
- Configurable

### Best Practices

```bash
# NUNCA hagas esto:
git add wrangler.synthesis.toml  # ❌ Contiene API keys

# En su lugar:
echo "wrangler.*.toml" >> .gitignore  # ✅ Excluir del repo
```

---

## 🐛 Troubleshooting

### Error: "DEEPSEEK_API_KEY is undefined"

**Solución:**
```bash
# Verificar que la key está en wrangler.synthesis.toml
cat wrangler.synthesis.toml | grep DEEPSEEK

# Re-deploy
npx wrangler deploy --config wrangler.synthesis.toml
```

### Error: "DeepSeek API rate limit"

**Causa:** Throttling dinámico en peak hours

**Solución:**
- El sistema automáticamente hace fallback a GPT-4o
- Implementar exponential backoff (ya incluido)

### Error: "Granted balance depleted"

**Solución:**
```bash
# 1. Ve a https://platform.deepseek.com/billing
# 2. Click "Top Up"
# 3. Agrega $20-50
# 4. Continue usando el servicio
```

---

## 📞 Soporte

**DeepSeek:**
- Docs: https://api-docs.deepseek.com
- Discord: https://discord.gg/deepseek
- Email: support@deepseek.com

**Cloudflare:**
- Docs: https://developers.cloudflare.com/workers/
- Community: https://community.cloudflare.com

---

## ✨ Próximos Pasos

1. ✅ Obtener DeepSeek API key
2. ✅ Configurar wrangler.synthesis.toml
3. ✅ Deploy del worker
4. 🧪 Test con 100-200 queries
5. 📊 Comparar calidad vs GPT-4o
6. 💰 Decidir si continuar (probablemente sí!)
7. 🚀 Disfrutar del 89% de ahorro

**Ahorro proyectado:**
- Mensual: $360 → $39 = **$321 ahorrados**
- Anual: $4,320 → $468 = **$3,852 ahorrados** 🎉
