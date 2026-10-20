"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api-client";

export default function LoginPage() {
  const [organizationCode, setOrganizationCode] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { signIn } = useAuth();
  const router = useRouter();

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await signIn({ organization_code: organizationCode, email, password });
      router.replace("/");
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Unable to sign in right now. Make sure the backend is running on port 8000.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-10">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(37,99,235,0.12),_transparent_42%),radial-gradient(circle_at_bottom_right,_rgba(249,115,22,0.1),_transparent_36%)]" />
      <Card className="relative w-full max-w-md overflow-hidden">
        <CardHeader className="border-0 pb-2">
          <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-sm font-bold text-primary-foreground">
            L
          </div>
          <CardTitle className="text-2xl font-semibold tracking-tight">Sign in to Labour ERP</CardTitle>
          <CardDescription>Use the demo account watermarks below. Signup is not needed.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-labour-ink">Organization code</span>
              <Input
                value={organizationCode}
                onChange={(event) => setOrganizationCode(event.target.value)}
                placeholder="demo"
                autoComplete="organization"
                required
              />
            </label>
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-labour-ink">Email</span>
              <Input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="admin@example.com"
                autoComplete="username"
                required
              />
            </label>
            <label className="block space-y-1.5">
              <span className="text-sm font-medium text-labour-ink">Password</span>
              <Input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="password123"
                autoComplete="current-password"
                required
              />
            </label>
            {errorMessage ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{errorMessage}</p> : null}
            <Button className="w-full" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <p className="mt-4 rounded-xl bg-muted px-3 py-2 text-xs leading-5 text-muted-foreground">
            Demo login: <span className="font-semibold text-foreground">demo</span> /{" "}
            <span className="font-semibold text-foreground">admin@example.com</span> /{" "}
            <span className="font-semibold text-foreground">password123</span>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
