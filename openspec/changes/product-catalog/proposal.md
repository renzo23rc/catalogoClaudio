# Proposal: Product Catalog

## Intent

Create a product catalog for a supermarket merchandise distributor, including a professional admin panel for stock management, daily offers, and a public catalog for clients.

## Scope

### In Scope
- Simple Product model (no variants, individual SKUs per item/presentation).
- Categories with self-referential hierarchy.
- ProductImage model for multiple photos per product.
- Flexible Offer model (percentage and fixed discounts, date ranges).
- Django Admin customizations for stock management, bulk updates, and export.
- Public catalog with homepage, category listing, product details, search, and filters.
- Local media storage setup (S3-ready).

### Out of Scope
- Shopping cart or checkout functionality (this is just a catalog).
- Complex product variants (e.g., sizes/colors on a single product).
- Payment gateway integration.
- User registration/auth for the public site.

## Capabilities

### New Capabilities
- `product-admin`: Admin panel for stock management, custom actions, and dashboard.
- `product-catalog`: Public catalog views including categories, details, search, and filters.
- `offer-management`: Daily offers system with flexible discount types and product associations.

### Modified Capabilities
- None

## Approach

Implement a Django project with two main apps: `products` and `offers`. Use Django's built-in Admin interface with heavy customizations (list displays, filters, inlines, bulk actions) to serve as the stock management panel. Build public views for the catalog using standard Django views/templates. Models will include `Category`, `Product`, `ProductImage`, and `Offer`. Configure media handling for local development with a path to migrate to S3.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `products/` | New | Django app for Category, Product, ProductImage models, Admin, and public views |
| `offers/` | New | Django app for Offer model and logic |
| `config/settings.py` | Modified | Add apps, configure media storage |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Admin panel UI/UX inadequate for fast stock updates | Medium | Implement custom bulk update actions and clean list_display |
| Image loading performance with many products | Low | Use pagination and optimize image delivery |

## Rollback Plan

Revert the git commit introducing the `products` and `offers` apps, drop the corresponding database tables (or migrate back to zero for these apps), and remove the apps from `INSTALLED_APPS`.

## Dependencies

- Django
- Pillow (for image handling)

## Success Criteria

- [ ] Admin can perform bulk stock updates and export product lists to CSV.
- [ ] Clients can browse the public catalog, view product details with multiple images, and see active offers.
- [ ] Products can be assigned to multiple categories and offers.
- [ ] Search and filtering functional on the public catalog.