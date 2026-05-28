# offer-management Specification

## Purpose

Defines the system for creating, scheduling, and managing daily offers and discounts applied to products.

## Requirements

### Requirement: Offer CRUD and Scheduling

The system MUST allow administrators to create offers with specific start and end dates.

#### Scenario: Schedule a future offer

- GIVEN an administrator creates a new offer
- WHEN they set a start date in the future and save
- THEN the offer remains inactive until the start date is reached

### Requirement: Discount Types

The system MUST support both percentage-based (e.g., 10% off) and fixed-amount (e.g., $5 off) discount types.

#### Scenario: Apply a percentage discount

- GIVEN an active percentage offer of 20%
- WHEN a product priced at $100 is assigned to it
- THEN the public catalog displays the product's effective price as $80

### Requirement: Product Assignment

The system MUST allow an offer to be assigned to one or more specific products.

#### Scenario: Assign products to an offer

- GIVEN an administrator is managing an offer
- WHEN they select multiple products to include in this offer
- THEN the discount is applied to all selected products

### Requirement: Active Offer Resolution

The system MUST ensure that when a product is displayed, its effective price reflects any active offer currently applied to it.

#### Scenario: View product with an active offer

- GIVEN a product is associated with an active offer
- WHEN a visitor views the product on the catalog
- THEN the original price is shown crossed out, and the new discounted price is highlighted
