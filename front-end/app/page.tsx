"use client";

import { useUser } from "@/providers/UserProvider";
import { signIn, signOut } from "@/utils/database_functions";

export default function Home() {
  const { user } = useUser();
  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="flex w-full max-w-md flex-col gap-3">
        <div className="text-sm">Status: {user === undefined ? "Checking..." : user ? `Logged in as ${user.email ?? user.displayName ?? user.uid}` : "Logged out"}</div>
        <div className="flex gap-3">
          <button onClick={signIn} className="rounded-md bg-zinc-900 px-3 py-2 text-white dark:bg-zinc-100 dark:text-black">Login</button>
          <button onClick={signOut} className="rounded-md border border-zinc-300 px-3 py-2 dark:border-zinc-700">Logout</button>
        </div>
      </div>
    </div>
  );
}
