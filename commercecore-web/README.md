# commercecore-web

The web app for CommerceCore: a storefront for customers and an admin console for the store.
It is the fifth project in this repo and only ever talks to the HTTP API in `commercecore-api`.

**Stack:** React 19 · TypeScript (strict) · Vite · Tailwind CSS v4 · React Router · TanStack Query · Vitest.

## Run it

From the repository root:

```bash
make run          # terminal 1: the API on http://127.0.0.1:8000
make seed         # once, on an empty dev database: demo data (password: password123)
make web-install  # once: npm packages (Node 20+)
make web          # terminal 2: the app on http://127.0.0.1:5173
make web-test     # type-check + tests + production build
```

Demo accounts after `make seed`: `sara@example.com` (customer) and `admin@commercecore.dev` (administrator).
On the login page, a **development-only** panel fills them in for you.

The API sends no CORS headers, so in development the browser calls `/api/...` on the Vite server, which
forwards to FastAPI and strips the `/api` prefix (`vite.config.ts`). For production, serve the built files
and the API from one origin with a reverse proxy, or set `VITE_API_URL`. See `.env.example`.

## What you can do

| Who | Screens |
|---|---|
| Anyone | Browse and search the shop, filter by category, sort, product details |
| Customer | Cart (kept in the browser), place an order, order history and progress |
| Administrator | Overview of what needs attention, confirm or cancel orders, create/edit products and stock, manage categories |

Rules from the API are respected in the UI and never re-implemented: the price always comes from the
server (the cart sends only product ids and quantities), stock limits stop the "+" button, a category
with products can't be deleted, and every refusal shows the API's own message.

## Structure

```
src/
  app/          router, providers, the two layouts (storefront, admin)
  pages/        one file per screen; pages/admin/ for the console (each page is its own chunk)
  features/     auth/ catalog/ cart/ orders/: data hooks (api.ts) and state, no markup
  components/   shared building blocks; ui/ holds the design-system primitives
  lib/          api client (the only place that calls fetch), types, formatting, cn()
  styles/       design tokens and Tailwind setup
```

Rules of the road:

- **Pages** compose components and call hooks from `features/*/api.ts`. They never call `fetch`.
- **`lib/api.ts`** owns HTTP: bearer token, error shape `{code, message, field}` → `ApiError`, sign-out on a rejected token.
- **Server state** lives in TanStack Query. After a write, the affected queries are invalidated (placing or cancelling an order refreshes stock everywhere).
- **Client state** is small and explicit: the session (`features/auth/session.ts`) and the cart (`features/cart/cart.ts`, a pure reducer with tests).
- **Filters are in the URL** (`?category=3&q=mug&sort=price-asc`), so views can be shared and Back works.

## Design

Warm paper-and-ink palette with one deep-teal accent, Fraunces for headings and Manrope for text.
The API has no product photos, so each product gets a generated tile (palette by category, pattern by id, its initials).

- Light and dark themes from the same semantic tokens (`styles/index.css`); the header toggle overrides the system setting.
- WCAG AA contrast in both themes, visible focus rings, 44 px touch targets, real labels on every field, errors beside the field, status shown with icon **and** text, a skip link, focus moved to the page on navigation, `prefers-reduced-motion` respected.
- Mobile first: the shop is one column on a phone, the admin sidebar becomes a tab strip.

## Security notes

- The access token is kept in `localStorage` so a reload doesn't sign you out. That is readable by any script on the page, so the app renders no untrusted HTML and keeps dependencies few.
- Route guards (`features/auth/guards.tsx`) are only a convenience. The API enforces who may do what.
