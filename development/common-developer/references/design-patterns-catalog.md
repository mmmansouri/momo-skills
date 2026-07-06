# Design Patterns — Decision Guide

> Decision surface only. GoF pattern implementations are standard knowledge and are intentionally not restated — pick with the table below, then apply the language's modern idiom (for Java specifics, load `common-java-developer` and read its `references/design-patterns.md`).

## Pattern Decision Guide

| Need | Pattern | Example |
|------|---------|---------|
| Create objects flexibly | Factory | PaymentMethodFactory |
| Build complex objects | Builder | Order.builder() |
| Multiple algorithms | Strategy | DiscountStrategy |
| Notify multiple objects | Observer | OrderConfirmedEvent |
| Algorithm template | Template Method | OrderProcessor |
| Adapt external API | Adapter | StripePaymentAdapter |
| Add features dynamically | Decorator | PriceCalculator decorators |

## Quick Checklist

- [ ] Pattern solves a real problem (not over-engineering)
- [ ] Pattern makes code more maintainable
- [ ] Pattern is well-known (team understands it)
- [ ] Pattern fits the domain model
- [ ] Simpler solution doesn't exist
