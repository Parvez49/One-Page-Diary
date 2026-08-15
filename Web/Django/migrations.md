# Migrations — Schema Change Without Downtime

> Models & fields: **[orm.md](orm.md)** · Deployment sequencing: **[deployment.md](deployment.md)**

---

## 1. The basics

```bash
python manage.py makemigrations app          # ⭐ generate from model changes
python manage.py makemigrations --name add_status_index app
python manage.py migrate                     # apply
python manage.py migrate app 0012            # ⭐ migrate to a specific point (rollback)
python manage.py migrate app zero            # unapply everything for an app

python manage.py showmigrations              # ⭐ what's applied ([X]) vs pending ([ ])
python manage.py sqlmigrate app 0013         # ⭐⭐ the actual SQL — READ THIS before deploying
python manage.py makemigrations --check --dry-run    # ⭐ CI gate: fail if models drifted
```

⭐ **`sqlmigrate` is the habit that separates seniors here.** It shows whether Django is about
to `ALTER TABLE` in a way that takes an `ACCESS EXCLUSIVE` lock and blocks every read on a
10-million-row table. Two seconds of reading prevents an outage.

**How Django tracks state:** applied migrations are rows in the **`django_migrations`** table.
Django compares them against the files on disk plus each migration's `dependencies` to build a
graph and compute what to run.

⚠️ **Migrations are code — commit them.** A model change without its migration file means the
next developer generates a conflicting one.

---

## 2. Anatomy

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("shop", "0012_product_slug")]      # ⭐ ordering, not just history

    operations = [
        migrations.AddField(
            model_name="product",
            name="status",
            field=models.CharField(max_length=20, default="draft"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["status"], name="idx_product_status"),
        ),
    ]
```

**Operation types:** `CreateModel`, `AddField`, `AlterField`, `RemoveField`, `RenameField`,
`AddIndex`, `AddConstraint`, `RunPython`, `RunSQL`, `SeparateDatabaseAndState`.

---

## 3. Data migrations

Schema and data changes must be **separate migrations** — mixing them makes rollback
impossible.

```python
def forwards(apps, schema_editor):
    Product = apps.get_model("shop", "Product")        # ⭐⭐ NEVER import the real model
    Product.objects.filter(status="").update(status="draft")

def backwards(apps, schema_editor):
    pass                                                # or the real inverse

class Migration(migrations.Migration):
    dependencies = [("shop", "0013_product_status")]
    operations = [
        migrations.RunPython(forwards, backwards),      # ⭐ always give a reverse
    ]
```

⭐⭐ **Always use `apps.get_model()`, never `from shop.models import Product`.** A data
migration runs against the **historical** schema as of that migration. The real model class
reflects *today's* fields — so a migration that imported it breaks the moment someone adds a
field later, and every fresh `migrate` from zero fails.

⚠️ **Historical models have no custom methods or managers** — only fields. Copy any helper
logic into the migration itself.

⚠️ **Don't iterate millions of rows in `RunPython`.** Use `.update()` with `F()`, or batch:

```python
qs = Product.objects.filter(status="")
while qs.exists():
    ids = list(qs.values_list("id", flat=True)[:5000])
    Product.objects.filter(id__in=ids).update(status="draft")
```

---

## 4. Zero-downtime schema changes ⭐⭐

**The core problem:** during a rolling deploy, **old and new code run simultaneously** against
**one database**. Every migration must be compatible with both.

### Locking — what's safe on Postgres

| Operation | Cost |
|---|---|
| `ADD COLUMN` (nullable, **no default**) | ⭐ instant, metadata only |
| `ADD COLUMN` with a default | ⭐ instant on **PG 11+**; ⚠️ full table rewrite before that |
| `ADD COLUMN NOT NULL` without default | ⚠️ fails / rewrites |
| `DROP COLUMN` | fast, but ⚠️ breaks old code still selecting it |
| `ALTER COLUMN TYPE` | ⚠️ **full rewrite + exclusive lock** |
| `RENAME COLUMN` | ⚠️ instant but **breaks all running old code** |
| `CREATE INDEX` | ⚠️ **blocks writes** — use `CONCURRENTLY` |
| `ADD CONSTRAINT` (validating) | ⚠️ full scan under lock |

⭐ **`AddIndexConcurrently`** — build an index without blocking writes:

```python
from django.contrib.postgres.operations import AddIndexConcurrently

class Migration(migrations.Migration):
    atomic = False                          # ⭐⭐ REQUIRED — can't run inside a transaction
    operations = [AddIndexConcurrently("product", models.Index(fields=["status"]))]
```

### The expand/contract pattern ⭐⭐

Never do a breaking change in one deploy. **Rename a column in four steps:**

```
1. EXPAND   add `full_name` (nullable). Deploy. Old code ignores it.
2. MIGRATE  backfill in batches; write to BOTH columns in app code.
3. SWITCH   deploy code that reads `full_name`. Old column now unused.
4. CONTRACT drop `name` in a later deploy.
```

Each step is independently deployable and reversible. A one-shot `RenameField` breaks every
old process still running mid-deploy.

**Adding a `NOT NULL` column safely:**

```
1. add nullable, with a default in the APPLICATION
2. backfill in batches
3. add the NOT NULL constraint (Postgres: ADD CONSTRAINT ... NOT VALID, then VALIDATE)
```

⚠️ **Never `makemigrations` a `NOT NULL` field on a populated table and deploy it blind** —
Django prompts for a one-off default, then rewrites the whole table under a lock.

---

## 5. Common problems

| Problem | Cause / fix |
|---|---|
| **Conflicting migrations** (two `0014_`) | parallel branches merged → `makemigrations --merge` |
| `InconsistentMigrationHistory` | applied out of dependency order — usually a rebased branch |
| **"No changes detected"** | app not in `INSTALLED_APPS`, or `makemigrations` without the app label |
| Migration works locally, fails in prod | different data — a constraint that existing rows violate |
| `RunPython` fails on fresh DB | ⭐ imported the real model instead of `apps.get_model()` |
| Need to undo an applied migration | `migrate app 0012` — ⚠️ only if the operations are reversible |
| **Squash for speed** | `squashmigrations app 0001 0042` after everyone has deployed |

⭐ **`--fake` is a scalpel, not a hammer:**

```bash
python manage.py migrate --fake app 0013         # mark applied WITHOUT running
python manage.py migrate --fake-initial          # ⭐ existing table, first migration
```

⚠️ `--fake` desynchronises the DB from migration state if you're wrong about what's already
there — the result is confusing failures weeks later.

---

## 6. Practices that hold up

- ⭐ **Review the generated migration before committing.** `makemigrations` produces
  `AlterField` for cosmetic changes (`help_text`, `verbose_name`) that still rewrite tables on
  some backends.
- ⭐ **One logical change per migration**, and separate schema from data.
- ⭐ **Always provide a reverse** for `RunPython` (`migrations.RunPython.noop` if genuinely
  irreversible) so a rollback isn't blocked.
- **Test the migration path**, not just the end state: `migrate zero && migrate` in CI, and
  test *backwards* for anything risky.
- **CI gate:** `makemigrations --check --dry-run` fails the build when a model changed without
  a migration.
- ⚠️ **Never edit an applied migration** on anything shared — the hash in `django_migrations`
  won't match and other environments diverge. Write a new one.
- ⚠️ **`RunSQL` needs `reverse_sql`** or the migration becomes irreversible.
- ⭐ For large-scale safety, `django-pg-zero-downtime-migrations` or `django-safemigrate` will
  refuse dangerous operations outright.

---

## 7. Interview points

- **How does Django know which migrations are applied?** Rows in the `django_migrations`
  table, plus the dependency graph across migration files.
- **Why `apps.get_model()` in a data migration? ⭐** It gives the **historical** model as of
  that migration; importing the real model breaks when the schema later changes.
- **How do you rename a column with zero downtime? ⭐⭐** Expand/contract — add the new column,
  dual-write and backfill, switch reads, drop the old one in a later deploy.
- **What makes a migration dangerous?** Locks: type changes, non-concurrent index creation,
  validating constraints, and any rewrite of a large table.
- **How do you add an index without blocking writes?** `AddIndexConcurrently` with
  `atomic = False` (Postgres).
- **Two branches produced conflicting migrations — now what?** `makemigrations --merge`, then
  verify the resulting order.
- **What does `--fake` do and when is it right?** Marks a migration applied without running
  it — for tables that already exist, e.g. adopting an existing database.
- **Should migrations be in version control?** Yes, always — they're part of the schema's
  history.
- **How do you make migrations reviewable?** `sqlmigrate` to read the SQL, one change per
  migration, and a CI check that models and migrations are in sync.
