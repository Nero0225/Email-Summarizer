# Database Migrations

This directory contains database migration files managed by Flask-Migrate (Alembic).

## Important Notes

### OAuth Users and Password Hash
The `password_hash` column in the `users` table is **nullable** to support OAuth authentication.
- Traditional users: Have a password_hash value
- OAuth users: Have password_hash = NULL

If you encounter `NOT NULL constraint failed: users.password_hash` errors, the database schema needs to be updated to allow NULL values.

## Common Commands

```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade to previous version
flask db downgrade

# View migration history
flask db history

# Show current migration version
flask db current
```

## Troubleshooting

If you get constraint errors with OAuth users:
1. The password_hash field must allow NULL values
2. Check the current schema with: `sqlite3 dev.db ".schema users"`
3. If needed, manually update the schema or recreate the database
