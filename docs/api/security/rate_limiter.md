# Rate Limiter

In-memory rate limiter for login attempts. Blocks a username after `MAX_ATTEMPTS` (5) failed attempts within `WINDOW_SECONDS` (900s / 15 min).

::: warriorfit.security.rate_limiter
    options:
      members_order: source
      show_source: true
