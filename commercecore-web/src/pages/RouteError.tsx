import { Compass } from "lucide-react";
import { Link, isRouteErrorResponse, useRouteError } from "react-router-dom";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/feedback";

export function NotFoundPage() {
  return (
    <EmptyState
      icon={<Compass className="size-6" aria-hidden />}
      title="Page not found"
      description="That address doesn't lead anywhere. It may have moved, or the link is mistyped."
      action={
        <Link to="/" className={buttonClass("primary")}>
          Back to the shop
        </Link>
      }
    />
  );
}

/** Shown when a page crashes or a route fails to load; the app never goes blank. */
export function RouteErrorBoundary() {
  const error = useRouteError();
  const notFound = isRouteErrorResponse(error) && error.status === 404;
  return (
    <div className="mx-auto max-w-xl px-4 py-16">
      {notFound ? (
        <NotFoundPage />
      ) : (
        <EmptyState
          title="Something went wrong"
          description="An unexpected error stopped this page from loading. Reloading usually fixes it."
          action={
            <button type="button" className={buttonClass("primary")} onClick={() => window.location.reload()}>
              Reload
            </button>
          }
        />
      )}
    </div>
  );
}
