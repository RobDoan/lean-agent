import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-xl p-6 text-center">
      <h1 className="text-2xl font-semibold">Not found</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        That page doesn't exist (or something went wrong loading it).
      </p>
      <p className="mt-4">
        <Link to="/" className="text-sm underline">
          ← back to dashboard
        </Link>
      </p>
    </main>
  );
}
