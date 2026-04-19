import Link from "next/link";
import { Show, SignInButton } from "@clerk/nextjs";

export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <div className="max-w-xl text-center space-y-6">
        <h1 className="text-4xl font-bold tracking-tight text-neutral-900">
          PlayerData Coaches Dashboard
        </h1>
        <p className="text-neutral-600">
          Athlete performance analytics powered by GPS/IMU session data.
        </p>

        <Show when="signed-out">
          <SignInButton mode="modal">
            <button className="rounded-md bg-emerald-500 px-5 py-2.5 font-semibold text-white hover:bg-emerald-600">
              Sign in to continue
            </button>
          </SignInButton>
        </Show>

        <Show when="signed-in">
          <Link
            href="/dashboard"
            className="inline-block rounded-md bg-emerald-500 px-5 py-2.5 font-semibold text-white hover:bg-emerald-600"
          >
            Open dashboard →
          </Link>
        </Show>
      </div>
    </main>
  );
}
