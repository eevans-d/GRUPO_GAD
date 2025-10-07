# Plan de Feedback y Mejora Continua - GRUPO_GAD

Este documento define el sistema de recopilación de feedback de usuarios, análisis de métricas de uso y proceso de mejora continua para el sistema GRUPO_GAD en producción.

## 1. Canales de Feedback

### 1.1. Feedback Directo de Usuarios

#### A. Bot de Telegram - Comando de Feedback
```python
# Implementación en el bot de Telegram
@bot.message_handler(commands=['feedback'])
def handle_feedback(message):
    """Recopilar feedback directo de usuarios via Telegram"""
    bot.reply_to(message, 
        "¡Gracias por tu interés en mejorar GRUPO_GAD! 📝\n\n"
        "Por favor, comparte tu feedback:\n"
        "• ¿Qué funciona bien?\n"
        "• ¿Qué podríamos mejorar?\n"
        "• ¿Qué características nuevas te gustarían?\n\n"
        "Responde a este mensaje con tus comentarios."
    )
    bot.register_next_step_handler(message, process_feedback)

def process_feedback(message):
    """Procesar y almacenar feedback"""
    feedback_data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "timestamp": datetime.now().isoformat(),
        "message": message.text,
        "platform": "telegram",
        "type": "general_feedback"
    }
    
    # Almacenar en base de datos
    store_feedback(feedback_data)
    
    # Notificar al equipo de desarrollo
    notify_development_team(feedback_data)
    
    bot.reply_to(message, 
        "✅ ¡Gracias por tu feedback! Lo hemos recibido y "
        "nuestro equipo lo revisará pronto."
    )
```

#### B. Endpoint de API para Feedback
```python
# Endpoint REST para feedback
@app.post("/api/v1/feedback")
async def submit_feedback(
    feedback: FeedbackSchema,
    current_user: User = Depends(get_current_user)
):
    """Endpoint para enviar feedback via API"""
    feedback_record = FeedbackModel(
        user_id=current_user.id,
        category=feedback.category,
        message=feedback.message,
        severity=feedback.severity,
        browser_info=feedback.browser_info,
        url=feedback.current_url,
        created_at=datetime.now()
    )
    
    db.add(feedback_record)
    await db.commit()
    
    # Analizar sentimiento automáticamente
    sentiment = analyze_sentiment(feedback.message)
    feedback_record.sentiment_score = sentiment
    
    # Clasificar automáticamente
    category = classify_feedback(feedback.message)
    feedback_record.auto_category = category
    
    await db.commit()
    
    return {"status": "success", "message": "Feedback recibido"}
```

### 1.2. Análisis de Comportamiento de Usuario

#### A. Métricas de Uso
```sql
-- Consultas para análisis de uso
-- Endpoints más utilizados
SELECT 
    endpoint,
    COUNT(*) as request_count,
    AVG(response_time) as avg_response_time,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
FROM api_logs 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY endpoint
ORDER BY request_count DESC;

-- Patrones de uso por horario
SELECT 
    EXTRACT(hour FROM created_at) as hour_of_day,
    COUNT(*) as request_count,
    COUNT(DISTINCT user_id) as unique_users
FROM api_logs 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Funcionalidades más utilizadas
SELECT 
    feature_name,
    COUNT(*) as usage_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(session_duration) as avg_session_time
FROM feature_usage_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY feature_name
ORDER BY usage_count DESC;
```

#### B. Análisis de Errores de Usuario
```python
# Sistema de tracking de errores de usuario
class UserErrorTracker:
    def __init__(self):
        self.error_patterns = {
            "validation_errors": r"validation.*error|invalid.*input",
            "permission_errors": r"access.*denied|permission.*error",
            "timeout_errors": r"timeout|request.*too.*long",
            "ui_errors": r"button.*not.*working|page.*not.*loading"
        }
    
    def track_error(self, user_id: int, error_type: str, 
                   context: dict, stack_trace: str = None):
        """Registrar errores de usuario para análisis"""
        error_record = UserErrorModel(
            user_id=user_id,
            error_type=error_type,
            context=json.dumps(context),
            stack_trace=stack_trace,
            created_at=datetime.now()
        )
        
        # Clasificar error automáticamente
        error_record.category = self.classify_error(error_type, context)
        
        # Determinar severidad
        error_record.severity = self.determine_severity(error_type, context)
        
        db.add(error_record)
        
        # Si es crítico, alertar inmediatamente
        if error_record.severity == "critical":
            self.alert_development_team(error_record)
    
    def generate_error_report(self, days: int = 7):
        """Generar reporte de errores más comunes"""
        return db.query(
            UserErrorModel.error_type,
            func.count().label('count'),
            func.count(UserErrorModel.user_id.distinct()).label('affected_users')
        ).filter(
            UserErrorModel.created_at >= datetime.now() - timedelta(days=days)
        ).group_by(UserErrorModel.error_type).all()
```

### 1.3. Surveys y Encuestas Programáticas

#### A. Net Promoter Score (NPS)
```python
# Sistema de NPS automático
class NPSManager:
    def __init__(self):
        self.survey_frequency = timedelta(days=30)  # Cada 30 días por usuario
    
    async def trigger_nps_survey(self, user_id: int):
        """Enviar survey NPS a usuario específico"""
        last_survey = await self.get_last_survey(user_id)
        
        if not last_survey or (datetime.now() - last_survey.created_at) > self.survey_frequency:
            # Enviar via Telegram si el usuario lo tiene habilitado
            if await self.user_has_telegram(user_id):
                await self.send_telegram_nps(user_id)
            
            # También enviar via email
            await self.send_email_nps(user_id)
    
    async def send_telegram_nps(self, user_id: int):
        """Enviar NPS via Telegram"""
        keyboard = types.InlineKeyboardMarkup()
        for i in range(0, 11):
            keyboard.add(
                types.InlineKeyboardButton(
                    str(i), 
                    callback_data=f"nps_{user_id}_{i}"
                )
            )
        
        message = (
            "📊 *Encuesta rápida de satisfacción*\n\n"
            "En una escala del 0 al 10, ¿qué tan probable es que "
            "recomiendes GRUPO_GAD a un colega?\n\n"
            "0 = Nada probable, 10 = Muy probable"
        )
        
        await bot.send_message(
            user_id, message, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
```

#### B. Encuestas de Funcionalidades Específicas
```python
# Encuestas contextuales después de usar funcionalidades
class FeatureFeedbackManager:
    def __init__(self):
        self.feedback_triggers = {
            "task_creation": {"threshold": 5, "delay": timedelta(minutes=5)},
            "report_generation": {"threshold": 3, "delay": timedelta(minutes=2)},
            "user_management": {"threshold": 2, "delay": timedelta(minutes=1)}
        }
    
    async def maybe_trigger_feedback(self, user_id: int, feature: str):
        """Activar feedback si se cumplen las condiciones"""
        usage_count = await self.get_feature_usage_count(user_id, feature)
        
        if usage_count == self.feedback_triggers[feature]["threshold"]:
            # Programar feedback con delay
            await self.schedule_feedback(
                user_id, 
                feature, 
                self.feedback_triggers[feature]["delay"]
            )
    
    async def send_feature_feedback(self, user_id: int, feature: str):
        """Enviar encuesta específica de funcionalidad"""
        questions = self.get_feature_questions(feature)
        
        survey_id = await self.create_survey(user_id, feature, questions)
        
        # Enviar primera pregunta
        await self.send_question(user_id, survey_id, 0)
```

## 2. Análisis y Procesamiento de Feedback

### 2.1. Análisis de Sentimientos

```python
# Análisis automático de sentimientos en feedback
from textblob import TextBlob
import re

class SentimentAnalyzer:
    def __init__(self):
        self.positive_keywords = [
            "excelente", "fantástico", "perfecto", "me encanta",
            "muy bueno", "impresionante", "útil", "fácil"
        ]
        self.negative_keywords = [
            "terrible", "horrible", "confuso", "lento", "error",
            "problema", "difícil", "complicado", "frustante"
        ]
    
    def analyze_sentiment(self, text: str) -> dict:
        """Analizar sentimiento de texto"""
        # Limpiar texto
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        
        # Análisis con TextBlob
        blob = TextBlob(clean_text)
        polarity = blob.sentiment.polarity  # -1 a 1
        subjectivity = blob.sentiment.subjectivity  # 0 a 1
        
        # Análisis con keywords
        positive_count = sum(1 for word in self.positive_keywords if word in clean_text)
        negative_count = sum(1 for word in self.negative_keywords if word in clean_text)
        
        # Clasificación final
        if polarity > 0.1 or positive_count > negative_count:
            sentiment = "positive"
        elif polarity < -0.1 or negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "polarity": polarity,
            "subjectivity": subjectivity,
            "confidence": abs(polarity) + (positive_count - negative_count) * 0.1
        }
```

### 2.2. Clasificación Automática de Feedback

```python
# Sistema de clasificación automática
class FeedbackClassifier:
    def __init__(self):
        self.categories = {
            "bug_report": {
                "keywords": ["error", "bug", "falla", "no funciona", "problema"],
                "patterns": [r"no.*funciona", r"error.*cuando", r"problema.*con"]
            },
            "feature_request": {
                "keywords": ["solicito", "me gustaría", "sería bueno", "nueva función"],
                "patterns": [r"sería.*bueno", r"me.*gustaría", r"podrían.*añadir"]
            },
            "ui_feedback": {
                "keywords": ["interfaz", "diseño", "botón", "página", "pantalla"],
                "patterns": [r"interfaz.*es", r"diseño.*de", r"botón.*no"]
            },
            "performance": {
                "keywords": ["lento", "rápido", "velocidad", "rendimiento", "carga"],
                "patterns": [r"muy.*lento", r"carga.*mucho", r"rendimiento.*malo"]
            },
            "general_praise": {
                "keywords": ["excelente", "me gusta", "fantástico", "perfecto"],
                "patterns": [r"me.*gusta", r"muy.*bueno", r"excelente.*trabajo"]
            }
        }
    
    def classify_feedback(self, text: str) -> str:
        """Clasificar feedback en categorías"""
        text_lower = text.lower()
        scores = {}
        
        for category, config in self.categories.items():
            score = 0
            
            # Puntuar por keywords
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    score += 1
            
            # Puntuar por patrones
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower):
                    score += 2
            
            scores[category] = score
        
        # Devolver categoría con mayor puntuación
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"
```

### 2.3. Priorización de Feedback

```python
# Sistema de priorización de feedback
class FeedbackPrioritizer:
    def __init__(self):
        self.priority_weights = {
            "user_count": 0.3,      # Cuántos usuarios reportan lo mismo
            "sentiment_score": 0.2,  # Qué tan negativo es el sentiment
            "feature_usage": 0.2,    # Qué tan usada es la funcionalidad
            "business_impact": 0.3   # Impacto en objetivos de negocio
        }
    
    def calculate_priority(self, feedback_item: dict) -> float:
        """Calcular prioridad de un item de feedback"""
        score = 0
        
        # Factor: Número de usuarios que reportan lo mismo
        similar_feedback_count = self.count_similar_feedback(feedback_item)
        user_factor = min(similar_feedback_count / 10, 1.0)  # Normalizar a 0-1
        score += user_factor * self.priority_weights["user_count"]
        
        # Factor: Sentiment (más negativo = mayor prioridad)
        sentiment_factor = 1.0 - (feedback_item.get("sentiment_score", 0) + 1) / 2
        score += sentiment_factor * self.priority_weights["sentiment_score"]
        
        # Factor: Uso de la funcionalidad afectada
        usage_factor = self.get_feature_usage_score(feedback_item.get("feature"))
        score += usage_factor * self.priority_weights["feature_usage"]
        
        # Factor: Impacto en negocio
        business_factor = self.assess_business_impact(feedback_item)
        score += business_factor * self.priority_weights["business_impact"]
        
        return score
    
    def get_prioritized_feedback_list(self, limit: int = 50) -> list:
        """Obtener lista priorizada de feedback"""
        all_feedback = self.get_all_pending_feedback()
        
        # Calcular prioridad para cada item
        for item in all_feedback:
            item["priority_score"] = self.calculate_priority(item)
        
        # Ordenar por prioridad
        return sorted(
            all_feedback, 
            key=lambda x: x["priority_score"], 
            reverse=True
        )[:limit]
```

## 3. Dashboard de Feedback

### 3.1. Métricas Clave de Feedback

```python
# Dashboard de métricas de feedback
class FeedbackDashboard:
    def get_feedback_metrics(self, days: int = 30) -> dict:
        """Obtener métricas de feedback para el dashboard"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Métricas básicas
        total_feedback = self.count_feedback(start_date, end_date)
        feedback_by_category = self.get_feedback_by_category(start_date, end_date)
        sentiment_distribution = self.get_sentiment_distribution(start_date, end_date)
        
        # Métricas de satisfacción
        nps_score = self.calculate_nps(start_date, end_date)
        satisfaction_trend = self.get_satisfaction_trend(days)
        
        # Métricas de respuesta
        avg_response_time = self.get_avg_response_time(start_date, end_date)
        resolution_rate = self.get_resolution_rate(start_date, end_date)
        
        return {
            "period": {"start": start_date, "end": end_date, "days": days},
            "volume": {
                "total_feedback": total_feedback,
                "daily_average": total_feedback / days,
                "by_category": feedback_by_category
            },
            "sentiment": {
                "distribution": sentiment_distribution,
                "nps_score": nps_score,
                "satisfaction_trend": satisfaction_trend
            },
            "response": {
                "avg_response_time_hours": avg_response_time,
                "resolution_rate_percent": resolution_rate
            }
        }
    
    def generate_feedback_report(self, period: str = "monthly") -> dict:
        """Generar reporte detallado de feedback"""
        if period == "weekly":
            days = 7
        elif period == "monthly":
            days = 30
        elif period == "quarterly":
            days = 90
        else:
            days = 30
        
        metrics = self.get_feedback_metrics(days)
        top_issues = self.get_top_issues(days)
        improvement_suggestions = self.get_improvement_suggestions(days)
        
        return {
            "report_period": period,
            "generated_at": datetime.now().isoformat(),
            "metrics": metrics,
            "top_issues": top_issues,
            "improvement_suggestions": improvement_suggestions,
            "action_items": self.generate_action_items(top_issues)
        }
```

### 3.2. Visualizaciones para el Dashboard

```python
# Generador de gráficos para dashboard
import plotly.graph_objects as go
import plotly.express as px

class FeedbackVisualizations:
    def create_sentiment_pie_chart(self, sentiment_data: dict):
        """Crear gráfico de pastel de distribución de sentimientos"""
        fig = go.Figure(data=[go.Pie(
            labels=list(sentiment_data.keys()),
            values=list(sentiment_data.values()),
            hole=.3,
            marker_colors=['#ff6b6b', '#ffd93d', '#6bcf7f']
        )])
        
        fig.update_layout(
            title="Distribución de Sentimientos en Feedback",
            annotations=[dict(text='Sentimientos', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        return fig.to_json()
    
    def create_feedback_trend_chart(self, trend_data: list):
        """Crear gráfico de tendencia de feedback"""
        dates = [item['date'] for item in trend_data]
        positive = [item['positive'] for item in trend_data]
        negative = [item['negative'] for item in trend_data]
        neutral = [item['neutral'] for item in trend_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=dates, y=positive, mode='lines+markers', name='Positivo', line=dict(color='#6bcf7f')))
        fig.add_trace(go.Scatter(x=dates, y=negative, mode='lines+markers', name='Negativo', line=dict(color='#ff6b6b')))
        fig.add_trace(go.Scatter(x=dates, y=neutral, mode='lines+markers', name='Neutral', line=dict(color='#ffd93d')))
        
        fig.update_layout(
            title="Tendencia de Feedback por Sentimiento",
            xaxis_title="Fecha",
            yaxis_title="Cantidad de Feedback",
            hovermode='x unified'
        )
        
        return fig.to_json()
    
    def create_nps_gauge(self, nps_score: float):
        """Crear gauge de NPS"""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = nps_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Net Promoter Score"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [-100, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [-100, 0], 'color': "lightgray"},
                    {'range': [0, 50], 'color': "gray"},
                    {'range': [50, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        return fig.to_json()
```

## 4. Proceso de Mejora Continua

### 4.1. Ciclo de Mejora Semanal

```python
# Proceso automatizado de mejora continua
class ContinuousImprovementManager:
    def __init__(self):
        self.improvement_cycle_days = 7
        self.min_feedback_threshold = 5
    
    async def weekly_improvement_cycle(self):
        """Ejecutar ciclo semanal de mejora"""
        print("🔄 Iniciando ciclo semanal de mejora continua")
        
        # 1. Recopilar y analizar feedback
        feedback_analysis = await self.analyze_weekly_feedback()
        
        # 2. Identificar patrones y problemas
        issues = await self.identify_priority_issues(feedback_analysis)
        
        # 3. Generar recomendaciones
        recommendations = await self.generate_recommendations(issues)
        
        # 4. Crear tickets de mejora
        tickets = await self.create_improvement_tickets(recommendations)
        
        # 5. Notificar al equipo
        await self.notify_team(feedback_analysis, recommendations, tickets)
        
        # 6. Programar seguimiento
        await self.schedule_follow_up(tickets)
        
        print(f"✅ Ciclo completado: {len(tickets)} tickets de mejora creados")
    
    async def generate_recommendations(self, issues: list) -> list:
        """Generar recomendaciones basadas en issues identificados"""
        recommendations = []
        
        for issue in issues:
            if issue["category"] == "performance":
                recommendations.extend(self.generate_performance_recommendations(issue))
            elif issue["category"] == "ui_feedback":
                recommendations.extend(self.generate_ui_recommendations(issue))
            elif issue["category"] == "bug_report":
                recommendations.extend(self.generate_bug_recommendations(issue))
            elif issue["category"] == "feature_request":
                recommendations.extend(self.generate_feature_recommendations(issue))
        
        # Priorizar recomendaciones
        return sorted(recommendations, key=lambda x: x["impact_score"], reverse=True)
    
    async def create_improvement_tickets(self, recommendations: list) -> list:
        """Crear tickets de mejora en el sistema de gestión"""
        tickets = []
        
        for rec in recommendations[:10]:  # Limitar a top 10
            ticket = {
                "title": rec["title"],
                "description": rec["description"],
                "priority": rec["priority"],
                "estimated_effort": rec["effort_hours"],
                "expected_impact": rec["impact_description"],
                "related_feedback": rec["feedback_ids"],
                "labels": ["continuous-improvement", rec["category"]],
                "created_at": datetime.now().isoformat()
            }
            
            # Crear en sistema de tickets (GitHub Issues, Jira, etc.)
            ticket_id = await self.create_ticket_in_system(ticket)
            ticket["id"] = ticket_id
            tickets.append(ticket)
        
        return tickets
```

### 4.2. Métricas de Mejora Continua

```sql
-- Consultas para medir efectividad de mejoras
-- Tendencia de satisfacción antes/después de implementar mejoras
WITH improvement_timeline AS (
    SELECT 
        deployment_date,
        feature_name,
        improvement_type
    FROM deployments 
    WHERE improvement_type IS NOT NULL
),
satisfaction_before_after AS (
    SELECT 
        it.feature_name,
        it.deployment_date,
        AVG(CASE 
            WHEN f.created_at BETWEEN it.deployment_date - INTERVAL '7 days' 
                                 AND it.deployment_date 
            THEN f.sentiment_score 
        END) as satisfaction_before,
        AVG(CASE 
            WHEN f.created_at BETWEEN it.deployment_date 
                                 AND it.deployment_date + INTERVAL '7 days' 
            THEN f.sentiment_score 
        END) as satisfaction_after
    FROM improvement_timeline it
    LEFT JOIN feedback f ON f.feature_name = it.feature_name
    GROUP BY it.feature_name, it.deployment_date
)
SELECT 
    feature_name,
    satisfaction_before,
    satisfaction_after,
    satisfaction_after - satisfaction_before as improvement_delta
FROM satisfaction_before_after
WHERE satisfaction_before IS NOT NULL 
  AND satisfaction_after IS NOT NULL
ORDER BY improvement_delta DESC;
```

### 4.3. Notificaciones al Equipo

```python
# Sistema de notificaciones para mejora continua
class ImprovementNotificationManager:
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_IMPROVEMENT_WEBHOOK")
        self.email_recipients = ["dev-team@grupogad.com", "product@grupogad.com"]
    
    async def notify_weekly_analysis(self, analysis: dict, recommendations: list):
        """Notificar análisis semanal al equipo"""
        message = self.format_weekly_message(analysis, recommendations)
        
        # Enviar a Slack
        await self.send_slack_notification(message)
        
        # Enviar email detallado
        await self.send_email_report(analysis, recommendations)
    
    def format_weekly_message(self, analysis: dict, recommendations: list) -> str:
        """Formatear mensaje para notificaciones"""
        top_recommendations = recommendations[:3]
        
        message = f"""
🔄 **Reporte Semanal de Mejora Continua - GRUPO_GAD**

📊 **Resumen de Feedback:**
• Total recibido: {analysis['total_feedback']}
• Sentiment promedio: {analysis['avg_sentiment']:.2f}
• Issues críticos: {analysis['critical_issues']}

🎯 **Top 3 Recomendaciones de Mejora:**
"""
        
        for i, rec in enumerate(top_recommendations, 1):
            message += f"""
{i}. **{rec['title']}**
   • Impacto esperado: {rec['impact_description']}
   • Esfuerzo estimado: {rec['effort_hours']}h
   • Prioridad: {rec['priority']}
"""
        
        message += f"\n📈 **Métricas de Mejora:**\n"
        message += f"• Tiempo promedio de resolución: {analysis['avg_resolution_time']:.1f}h\n"
        message += f"• Tasa de implementación: {analysis['implementation_rate']:.1f}%\n"
        
        return message
```

## 5. Métricas de Éxito

### 5.1. KPIs de Feedback

| Métrica | Objetivo | Frecuencia |
|---------|----------|------------|
| Net Promoter Score (NPS) | > 50 | Mensual |
| Tiempo de respuesta a feedback | < 24h | Diario |
| Tasa de resolución de issues | > 80% | Semanal |
| Satisfacción promedio | > 4.0/5.0 | Semanal |
| Feedback por usuario activo | > 0.1 | Mensual |

### 5.2. Métricas de Mejora Continua

| Métrica | Objetivo | Frecuencia |
|---------|----------|------------|
| Issues implementados por sprint | > 5 | Quincenal |
| Mejora en sentiment post-implementación | > +0.2 | Por release |
| Reducción de reportes de bugs | -10% mensual | Mensual |
| Incremento en engagement | +5% mensual | Mensual |

## 6. Automatización y Herramientas

### 6.1. Cron Jobs para Análisis

```bash
# /etc/cron.d/grupogad-feedback

# Análisis diario de feedback
0 9 * * * deploy /opt/grupogad/scripts/daily_feedback_analysis.py

# Reporte semanal de mejora continua
0 10 * * 1 deploy /opt/grupogad/scripts/weekly_improvement_cycle.py

# Encuestas NPS mensuales
0 9 1 * * deploy /opt/grupogad/scripts/trigger_monthly_nps.py

# Limpieza de feedback antiguo
0 2 1 * * deploy /opt/grupogad/scripts/cleanup_old_feedback.py
```

### 6.2. Integración con Herramientas Externas

- **GitHub Issues**: Creación automática de tickets de mejora
- **Slack/Discord**: Notificaciones de feedback crítico
- **Google Analytics**: Correlación con métricas de uso
- **Hotjar/FullStory**: Análisis de comportamiento de usuario
- **Tableau/PowerBI**: Dashboards ejecutivos de feedback

---

## Referencias

- [Customer Feedback Management Best Practices](https://blog.hubspot.com/service/what-does-it-mean-to-be-customer-centric)
- [NPS Methodology](https://www.netpromoter.com/know/)
- [Continuous Improvement in Software](https://www.atlassian.com/continuous-delivery/principles/continuous-improvement)
- [Sentiment Analysis Techniques](https://monkeylearn.com/sentiment-analysis/)