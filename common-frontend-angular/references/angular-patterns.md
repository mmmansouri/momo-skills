# Angular Patterns Reference

## NgRx Signal Store (Angular 17+)

```typescript
import { signalStore, withState, withComputed, withMethods, patchState } from '@ngrx/signals';

interface ProductsState {
  products: Product[];
  loading: boolean;
  filter: string;
}

export const ProductsStore = signalStore(
  { providedIn: 'root' },
  withState<ProductsState>({
    products: [],
    loading: false,
    filter: ''
  }),
  withComputed((store) => ({
    filteredProducts: computed(() => {
      const filter = store.filter().toLowerCase();
      return store.products().filter(p =>
        p.name.toLowerCase().includes(filter)
      );
    }),
    productCount: computed(() => store.products().length)
  })),
  withMethods((store, productsService = inject(ProductsService)) => ({
    async loadProducts() {
      patchState(store, { loading: true });
      const products = await firstValueFrom(productsService.getAll());
      patchState(store, { products, loading: false });
    },
    setFilter(filter: string) {
      patchState(store, { filter });
    }
  }))
);
```

---

## Typed Reactive Forms

```typescript
import { FormBuilder, FormControl, Validators } from '@angular/forms';

interface LoginForm {
  email: FormControl<string>;
  password: FormControl<string>;
  rememberMe: FormControl<boolean>;
}

@Component({...})
export class LoginComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group<LoginForm>({
    email: this.fb.control('', {
      nonNullable: true,
      validators: [Validators.required, Validators.email]
    }),
    password: this.fb.control('', {
      nonNullable: true,
      validators: [Validators.required, Validators.minLength(8)]
    }),
    rememberMe: this.fb.control(false, { nonNullable: true })
  });

  onSubmit() {
    if (this.form.valid) {
      const { email, password, rememberMe } = this.form.getRawValue();
    }
  }
}
```

---

## HTTP with Signals

```typescript
import { HttpClient } from '@angular/common/http';
import { toSignal } from '@angular/core/rxjs-interop';

@Injectable({ providedIn: 'root' })
export class ProductService {
  private http = inject(HttpClient);

  getProducts(): Observable<Product[]> {
    return this.http.get<Product[]>('/api/products');
  }

  readonly products = toSignal(this.getProducts(), { initialValue: [] });
}
```

### Functional Interceptors (Angular 15+)

```typescript
import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).getToken();

  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }

  return next(req);
};

// app.config.ts — Angular 21+: HttpClient auto-provided, provideHttpClient() only needed for interceptors
export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withInterceptors([authInterceptor]))
  ]
};
```

---

## Routing (Standalone)

### Functional Guards (Angular 15+)

```typescript
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url }
  });
};
```

### Route Configuration

```typescript
export const routes: Routes = [
  { path: '', component: HomeComponent },
  {
    path: 'products',
    loadComponent: () => import('./features/catalog/product-list.component')
      .then(m => m.ProductListComponent)
  },
  {
    path: 'admin',
    canActivate: [authGuard],
    loadChildren: () => import('./features/admin/routes')
      .then(m => m.ADMIN_ROUTES)
  }
];
```

---

## Resource API (Angular 21+)

### Declarative Data Fetching

```typescript
import { resource, Signal } from '@angular/core';

@Component({...})
export class ProductDetailComponent {
  readonly productId = input.required<string>();

  readonly productResource = resource({
    request: () => this.productId(),
    loader: async ({ request: id }) => {
      const response = await fetch(`/api/products/${id}`);
      return response.json() as Promise<Product>;
    }
  });
}
```

```html
@switch (productResource.status()) {
  @case ('loading') { <app-spinner /> }
  @case ('error') { <p>Error: {{ productResource.error()?.message }}</p> }
  @case ('resolved') { <app-product-detail [product]="productResource.value()!" /> }
}
```
