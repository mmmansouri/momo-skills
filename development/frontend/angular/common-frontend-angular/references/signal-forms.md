# Signal Forms (Angular 21+ Experimental)

> **Status:** Experimental — API may change. Do NOT adopt in production yet.

## Signal-Based Forms

```typescript
import { form, FormField } from '@angular/forms';
import { Validators } from '@angular/forms';

@Component({
  template: `
    <form (ngSubmit)="onSubmit()">
      <input [formField]="loginForm.controls.email" />
      <input [formField]="loginForm.controls.password" type="password" />
      <button type="submit" [disabled]="loginForm.invalid()">Login</button>
    </form>
  `
})
export class LoginComponent {
  readonly loginForm = form({
    email: ['', Validators.required, Validators.email],
    password: ['', Validators.required, Validators.minLength(8)],
  });

  onSubmit() {
    if (this.loginForm.valid()) {
      const { email, password } = this.loginForm.value();
      // Fully typed, signal-based!
    }
  }
}
```

## Key Differences from Reactive Forms

| Reactive Forms | Signal Forms |
|---------------|-------------|
| `FormControl`, `FormGroup` | `form()`, `FormField` |
| `[formControl]` directive | `[formField]` directive |
| `.value` (property) | `.value()` (signal) |
| `.valid` (property) | `.valid()` (signal) |
| Requires `ReactiveFormsModule` | Standalone, signal-native |

> **Note:** Reactive Forms remain fully supported. Signal Forms are an experimental alternative.
