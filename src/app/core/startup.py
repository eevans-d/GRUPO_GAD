from .config import settings

def validate_environment() -> None:
    # Validaciones basadas en settings (no en os.getenv)
    problems = []

    if len(settings.SECRET_KEY) < 32:
        problems.append("SECRET_KEY length < 32")
    if len(settings.JWT_SECRET_KEY) < 32:
        problems.append("JWT_SECRET_KEY length < 32")
    if settings.JWT_ALGORITHM not in {"HS256", "HS384", "HS512", "RS256"}:
        problems.append("JWT_ALGORITHM inválido")
    if settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        problems.append("ACCESS_TOKEN_EXPIRE_MINUTES debe ser > 0")
    if settings.ENVIRONMENT not in {"development", "staging", "production"}:
        problems.append("ENVIRONMENT inválido")
    if settings.ENVIRONMENT == "production":
        if settings.DATABASE_URL.startswith("sqlite"):
            problems.append("DATABASE_URL no puede ser sqlite en producción")
        if "dev-insecure" in settings.SECRET_KEY or "dev-insecure" in settings.JWT_SECRET_KEY:
            problems.append("SECRET_KEY/JWT_SECRET_KEY de desarrollo en producción")

    if problems:
        msg = " | ".join(problems)
        raise RuntimeError(f"Environment validation failed: {msg}")
