# Design: Product Catalog

## Technical Approach

Greenfield Django 5.x project with two apps — `products` (Category, Product, ProductImage) and `offers` (Offer) — plus project config `catalogo/`. Django Admin serves as the stock management panel with heavy customizations. Public catalog uses class-based generic views with server-rendered templates. Local media storage configured via `MEDIA_ROOT`/`MEDIA_URL`, structured for future S3 migration with django-storages.

## Architecture Decisions

### Decision: Settings Structure

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Single `settings.py` with `python-dotenv` | Simple, fast to iterate | **Chosen** |
| Split `settings/base.py` + `dev.py`/`prod.py` | Overhead without multi-env deployment yet | Deferred |

**Rationale**: Greenfield with one environment (SQLite dev). Split when staging/production diverge. Use `python-dotenv` for secrets from day one.

### Decision: URL Structure

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Spanish RESTful slugs (`/categoria/<slug>/`) | Matches domain language, predictable | **Chosen** |
| English `/category/<slug>/` | Generic but mismatch for supermarket audience | Rejected |
| ID-based (`/product/42/`) | SEO-unfriendly, opaque | Rejected |

**Rationale**: Spanish slugs match the supermarket distributor domain. SEO-friendly, human-readable. URL patterns: `/`, `/categoria/<slug>/`, `/producto/<slug>/`, `/buscar/?q=...`.

### Decision: Admin Customization Strategy

**Choice**: Heavy admin customization via `ModelAdmin` subclasses — `list_display`, `list_filter`, `search_fields`, `inlines` (ProductImage inline on Product), custom bulk actions (stock update, CSV export), custom `list_editable` for quick stock edits.

**Rationale**: The Django Admin *is* the stock management panel. No separate dashboard needed. Bulk actions handle the "professional admin panel" requirement without building custom views.

### Decision: Image Upload Path

**Choice**: `upload_to` callable generating `products/<sku>/<filename>`. Primary image identified via `is_primary` boolean on ProductImage.

```python
def product_image_path(instance, filename):
    return f"products/{instance.product.sku}/{filename}"
```

**Rationale**: SKU is the stable business identifier. Category-based paths break when products move categories. Organization per-product keeps related images together.

### Decision: Template Approach

| Option | Tradeoff | Decision |
|--------|----------|----------|
| CBV (`ListView`, `DetailView`) | Django-native, built-in pagination, method override pattern | **Chosen** |
| FBV | More explicit but more boilerplate for list/detail | Rejected |

**Rationale**: `ListView` gives pagination, `get_queryset()` overrides for filtering, `get_context_data()` for extra context. Less code, same control.

### Decision: Offer Discount Evaluation

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `@property` on Offer model | Simple, readable, per-instance only | **Chosen for phase 1** |
| Queryset annotation | Efficient for listing pages with many products | Deferred |

**Rationale**: Phase 1 has hundreds of products — `@property` is fast enough. If offer-heavy listing pages slow down, migrate to `annotate()` with `Case`/`When`.

### Decision: Search Implementation

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `icontains` on `name` + `description` | SQLite-compatible, zero setup | **Chosen for phase 1** |
| PostgreSQL `SearchVector` + `SearchRank` | Proper full-text, but requires PostgreSQL | Deferred |

**Rationale**: SQLite for dev, no external search dependency. `icontains` works for hundreds of products. Migrate to PostgreSQL full-text when data exceeds ~10K rows.

## Data Flow

```
Browser ──GET──→ URL Dispatcher ──→ CBV (ListView/DetailView)
                                        │
                                   ORM Query (with filters/icontains)
                                        │
                                     SQLite
                                        │
                                   Template render ←── context + objects
                                        │
Browser ←──HTML─────────────────────────┘

Admin: Browser ──→ AdminSite ──→ ModelAdmin ──→ ORM ──→ admin template
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `manage.py` | Create | Django project entry point |
| `catalogo/__init__.py` | Create | Project package |
| `catalogo/settings.py` | Create | Single settings with dotenv, SQLite, media config |
| `catalogo/urls.py` | Create | Root URLconf: `/admin/`, `/media/`, public catalog include |
| `catalogo/wsgi.py` | Create | WSGI application |
| `catalogo/asgi.py` | Create | ASGI application |
| `products/__init__.py` | Create | App package |
| `products/models/__init__.py` | Create | Re-export Category, Product, ProductImage |
| `products/models/category.py` | Create | Category model (self-referential FK) |
| `products/models/product.py` | Create | Product model (SKU, Decimal price, stock) |
| `products/models/image.py` | Create | ProductImage model (upload_to, is_primary, order) |
| `products/admin.py` | Create | Admin configs with inlines, bulk actions, CSV export |
| `products/views.py` | Create | CBVs: HomeView, CategoryListView, ProductDetailView, SearchView |
| `products/urls.py` | Create | Public URL patterns |
| `products/templates/products/` | Create | Templates: home, category_list, product_detail, search |
| `offers/__init__.py` | Create | App package |
| `offers/models.py` | Create | Offer model (discount_type, value, dates, M2M to Product) |
| `offers/admin.py` | Create | Offer ModelAdmin with filter_horizontal for products |
| `requirements.txt` | Create | Django, Pillow, python-dotenv |
| `static/css/` | Create | Base CSS for public catalog |
| `media/` | Create | Upload root (gitignored) |

## Interfaces / Contracts

### URL Patterns
```python
# products/urls.py
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("categoria/<slug:slug>/", CategoryListView.as_view(), name="category"),
    path("producto/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path("buscar/", SearchView.as_view(), name="search"),
]
```

### Model Signatures
```python
class Category(models.Model):
    name, slug (unique), description, parent (FK self, null), is_active, created_at

class Product(models.Model):
    name, slug (unique), sku (unique), description, base_price (Decimal(10,2)),
    category (FK Category), stock_quantity (PositiveInteger), is_active, created_at, updated_at

class ProductImage(models.Model):
    product (FK Product), image, is_primary, alt_text, order

class Offer(models.Model):
    name, description, discount_type (percentage/fixed), discount_value,
    start_date, end_date, is_active, products (M2M Product), created_at
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit — Models | Slug generation, discount calculation, upload paths | `pytest-django` with model instances |
| Unit — Admin | List display, filters, bulk actions | Django `AdminSite` test client |
| Integration — Views | Public catalog rendering, search, filtering | `pytest-django` with `Client` + test fixtures |
| Integration — Media | Image upload, path generation | `pytest-django` with `MEDIA_ROOT` override |

## Migration / Rollout

No migration required (greenfield). Run `migrate` after `makemigrations`, load fixture data for development.

## Open Questions

None.
