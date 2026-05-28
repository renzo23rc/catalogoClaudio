# Tasks: Product Catalog

**Change**: `product-catalog`  
**Created**: 2026-05-28  
**Mode**: hybrid

---

## Phase 1: Project Setup (Files 1-8)

### 1.1 Create Django project structure
- [x] `manage.py` — Django project entry point
- [x] `catalogo/__init__.py` — Project package marker
- [x] `catalogo/settings.py` — Single settings with `python-dotenv`, SQLite, media config
- [x] `catalogo/urls.py` — Root URLconf: `/admin/`, `/media/`, public catalog include
- [x] `catalogo/wsgi.py` — WSGI application
- [x] `catalogo/asgi.py` — ASGI application

**Acceptance Criteria**:
- `python manage.py check` runs without errors
- Settings loads environment variables via `python-dotenv`
- Media root configured to `/media/` directory

### 1.2 Create requirements and static assets
- [x] `requirements.txt` — Django, Pillow, python-dotenv
- [x] `static/css/base.css` — Base CSS for public catalog
- [x] `media/.gitkeep` — Upload root placeholder (gitignored)

**Acceptance Criteria**:
- `pip install -r requirements.txt` installs all dependencies
- Static directory exists for collectstatic

---

## Phase 2: Products App - Models (Files 9-13)

### 2.1 Create products app package
- [x] `products/__init__.py` — App package marker

### 2.2 Create Category model
- [x] `products/models/category.py`
  - Fields: `name`, `slug` (unique), `description`, `parent` (FK self, null/blank), `is_active`, `created_at`
  - Meta: ordering by `name`
  - `__str__`: returns name with parent prefix if applicable

**Acceptance Criteria**:
- Self-referential hierarchy works (parent can be null)
- Slug is unique across all categories
- Inactive categories can be hidden from public views

### 2.3 Create Product model
- [x] `products/models/product.py`
  - Fields: `name`, `slug` (unique), `sku` (unique), `description`, `base_price` (Decimal(10,2)), `category` (FK Category), `stock_quantity` (PositiveIntegerField), `is_active`, `created_at`, `updated_at`
  - Meta: ordering by `-created_at`
  - `__str__`: returns name

**Acceptance Criteria**:
- SKU is unique (business identifier)
- Price uses Decimal for precision
- Stock quantity cannot be negative

### 2.4 Create ProductImage model
- [x] `products/models/image.py`
  - Fields: `product` (FK Product, related_name='images'), `image` (ImageField), `is_primary` (Boolean), `alt_text`, `order` (PositiveIntegerField)
  - `upload_to` callable: `products/<sku>/<filename>`
  - Meta: ordering by `order`

**Acceptance Criteria**:
- Images upload to SKU-based directory structure
- One primary image per product can be marked
- Order field controls display sequence

### 2.5 Create models package export
- [x] `products/models/__init__.py` — Re-export Category, Product, ProductImage

**Acceptance Criteria**:
- `from products.models import Category, Product, ProductImage` works

---

## Phase 3: Products App - Admin & Views (Files 14-16)

### 3.1 Create Product admin configuration
- [x] `products/admin.py`
  - ProductImageInline (TabularInline)
  - ProductAdmin with:
    - `list_display`: name, sku, category, stock_quantity, base_price, is_active
    - `list_filter`: category, is_active, stock_quantity (low stock filter)
    - `search_fields`: name, sku, description
    - `list_editable`: stock_quantity (quick edit)
    - `inlines`: [ProductImageInline]
    - Custom bulk actions: "Export to CSV", "Mark as inactive", "Update stock"
    - CSV export action
  - CategoryAdmin with:
    - `list_display`: name, parent, is_active
    - `list_filter`: is_active, parent
  - ProductImageAdmin (minimal)

**Acceptance Criteria**:
- Admin can edit stock directly from list view
- Bulk CSV export downloads selected products
- Low stock filter shows products below threshold (e.g., <10 units)
- Images can be added inline on product edit page

### 3.2 Create public catalog views
- [x] `products/views.py`
  - `HomeView` (TemplateView): Display root categories, featured products, active offers
  - `CategoryListView` (ListView): Paginated product grid for category + subcategories
  - `ProductDetailView` (DetailView): Product details with image gallery
  - `SearchView` (ListView): Search results with `icontains` on name/description

**Acceptance Criteria**:
- Homepage shows root categories and offers section
- Category view includes products from subcategories
- Product detail shows all images with primary first
- Search supports `?q=` query parameter

### 3.3 Create products URL patterns
- [x] `products/urls.py`
  ```python
  urlpatterns = [
      path("", HomeView.as_view(), name="home"),
      path("categoria/<slug:slug>/", CategoryListView.as_view(), name="category"),
      path("producto/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
      path("buscar/", SearchView.as_view(), name="search"),
  ]
  ```

**Acceptance Criteria**:
- URL patterns match spec (Spanish slugs)
- All views are accessible via named URLs

---

## Phase 4: Products App - Templates (Files 17-20)

### 4.1 Create base template
- [x] `products/templates/products/base.html`
  - HTML5 boilerplate with `{% block content %}`
  - Include base.css
  - Navigation with search bar

### 4.2 Create homepage template
- [x] `products/templates/products/home.html`
  - Root categories grid
  - Featured products section
  - Active offers section

### 4.3 Create category list template
- [x] `products/templates/products/category_list.html`
  - Category title and description
  - Product grid with pagination
  - Filter sidebar (category, price range, on offer toggle)

### 4.4 Create product detail template
- [x] `products/templates/products/product_detail.html`
  - Product name, SKU, description
  - Price display (with offer discount if active)
  - Stock availability indicator
  - Image gallery (primary + thumbnails)

### 4.5 Create search template
- [x] `products/templates/products/search.html`
  - Search form with current query
  - Results grid (same as category list)
  - "No results" message

**Acceptance Criteria for all templates**:
- Extend base.html correctly
- Use Django template language for dynamic content
- Responsive grid layout for products
- Pagination controls where applicable

---

## Phase 5: Offers App (Files 21-23)

### 5.1 Create offers app package
- [x] `offers/__init__.py` — App package marker

### 5.2 Create Offer model
- [x] `offers/models.py`
  - Fields: `name`, `description`, `discount_type` (choices: percentage/fixed), `discount_value` (Decimal(10,2)), `start_date`, `end_date`, `is_active`, `products` (M2M Product, related_name='offers'), `created_at`
  - Property `is_currently_active`: checks dates + is_active flag
  - Method `get_discounted_price(product)`: calculates effective price
  - Meta: ordering by `-start_date`

**Acceptance Criteria**:
- Discount type restricts to percentage or fixed
- `is_currently_active` returns True only if within date range AND is_active=True
- `get_discounted_price` returns correct price after discount
- M2M allows one offer to apply to multiple products

### 5.3 Create Offer admin configuration
- [x] `offers/admin.py`
  - OfferAdmin with:
    - `list_display`: name, discount_type, discount_value, start_date, end_date, is_currently_active
    - `list_filter`: discount_type, is_active, start_date, end_date
    - `search_fields`: name, description
    - `filter_horizontal`: products (for easy M2M selection)
    - Date hierarchy for navigation

**Acceptance Criteria**:
- Admin can see which offers are currently active
- Product selection uses horizontal filter widget
- Date-based navigation works

---

## Phase 6: Integration & Configuration (Files 24-26)

### 6.1 Update project URLs
- [x] Modify `catalogo/urls.py`
  - Include admin: `path('admin/', admin.site.urls)`
  - Include products app: `path('', include('products.urls'))`
  - Serve media in development: `static(settings.MEDIA_URL, ...)`

**Acceptance Criteria**:
- `/admin/` accessible
- Root URL serves products app
- Media files served in development

### 6.2 Update settings
- [x] Modify `catalogo/settings.py`
  - Add `'products'` and `'offers'` to `INSTALLED_APPS`
  - Configure `MEDIA_ROOT` and `MEDIA_URL`
  - Set up `python-dotenv` integration

**Acceptance Criteria**:
- Apps register correctly
- Media uploads save to `/media/` directory
- Environment variables load from `.env`

### 6.3 Create migrations and test
- [x] Run `python manage.py makemigrations`
- [x] Run `python manage.py migrate`
- [x] Create superuser for admin testing
- [x] Verify all models migrate without errors

**Acceptance Criteria**:
- Migrations create all tables
- No migration errors
- Admin is accessible with superuser

---

## Summary

**Total Files**: 26 files across 6 phases

| Phase | Files | Focus |
|-------|-------|-------|
| 1 | 8 | Project setup (config, requirements, static) |
| 2 | 5 | Products app models (Category, Product, ProductImage) |
| 3 | 3 | Products app admin & views |
| 4 | 5 | Products app templates |
| 5 | 3 | Offers app (model + admin) |
| 6 | 3 | Integration (URLs, settings, migrations) |

**Estimated Review Workload**: 600-800+ lines
- Models: ~150 lines
- Admin: ~120 lines
- Views: ~100 lines
- Templates: ~200-300 lines (5 templates × 40-60 lines each)
- URL patterns: ~30 lines
- Settings/URLs config: ~50 lines
- Other (init files, requirements, CSS): ~50 lines

**Dependencies Between Phases**:
- Phase 2 must complete before Phase 3 (models before views/admin)
- Phase 3 must complete before Phase 4 (views before templates)
- Phase 5 can run parallel to Phase 2-4 (independent app)
- Phase 6 is final integration after all apps exist

---

## Progress Tracking

**Completed**: [1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 6.1, 6.2, 6.3]
**In Progress**: []
**Pending**: []
