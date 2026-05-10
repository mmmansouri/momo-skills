# Angular Migration Checklist (from Angular 16 or earlier)

## Phase 1: Control Flow Migration
```bash
ng generate @angular/core:control-flow
```

## Phase 2: Signal Inputs/Outputs
```bash
ng generate @angular/core:signal-input-migration
ng generate @angular/core:signal-output-migration
```

## Phase 3: Signal Queries
```bash
ng generate @angular/core:signal-queries-migration
```

## Phase 4: ngClass/ngStyle Migration (Angular 21+)
```bash
ng generate @angular/core:class-migration    # [ngClass] -> [class]
ng generate @angular/core:style-migration    # [ngStyle] -> [style]
```

## Phase 5: Zoneless Migration (Angular 21+)
1. Replace `provideZoneChangeDetection()` with `provideZonelessChangeDetection()`
2. Remove `zone.js` from `polyfills` in `angular.json`
3. Ensure all state uses Signals (no zone.js-dependent change detection)
