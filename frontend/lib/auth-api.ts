import { z } from "zod";

const userSchema = z.object({
  public_id: z.string().uuid(),
  email: z.string().email(),
  first_name: z.string(),
  last_name: z.string(),
  phone: z.string(),
  preferred_locale: z.string(),
  email_verified: z.boolean(),
  is_staff: z.boolean().optional(),
});

const sessionSchema = z.object({ user: userSchema });
const messageSchema = z.object({ message: z.string() });
const csrfSchema = z.object({ csrf_token: z.string().min(1) });

export type AccountUser = z.infer<typeof userSchema>;

type ErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    fields?: Record<string, unknown> | null;
    request_id?: string | null;
  };
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code = "request_error",
    public readonly fields: Record<string, unknown> | null = null,
  ) {
    super(message);
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let payload: ErrorEnvelope = {};
  try {
    payload = (await response.json()) as ErrorEnvelope;
  } catch {
    // Django may return an HTML CSRF rejection. Keep the public message generic.
  }
  return new ApiError(
    payload.error?.message ?? "La demande n’a pas pu être traitée.",
    response.status,
    payload.error?.code,
    payload.error?.fields ?? null,
  );
}

async function csrfToken(): Promise<string> {
  const response = await fetch("/api/v1/auth/csrf/", {
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) throw await parseError(response);
  return csrfSchema.parse(await response.json()).csrf_token;
}

async function mutate(path: string, method: "POST" | "PATCH", body?: unknown) {
  const token = await csrfToken();
  const response = await fetch(path, {
    method,
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": token,
    },
    body: JSON.stringify(body ?? {}),
  });
  if (!response.ok) throw await parseError(response);
  return response;
}

export async function mutateWithCsrf(path: string, init: { method: "POST" | "PATCH"; body?: string }) {
  const token = await csrfToken();
  const response = await fetch(path, {
    ...init,
    credentials: "same-origin",
    cache: "no-store",
    headers: { "Content-Type": "application/json", "X-CSRFToken": token },
  });
  if (!response.ok) throw await parseError(response);
  return response.json();
}

export async function registerAccount(input: {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  password: string;
  accept_terms: boolean;
  accept_privacy: boolean;
}) {
  const response = await mutate("/api/v1/auth/register/", "POST", input);
  return z.object({ message: z.string(), verification_email_sent: z.boolean() }).parse(await response.json());
}

export async function loginAccount(email: string, password: string): Promise<AccountUser> {
  const response = await mutate("/api/v1/auth/login/", "POST", { email, password });
  return sessionSchema.parse(await response.json()).user;
}

export async function logoutAccount(): Promise<void> {
  const response = await mutate("/api/v1/auth/logout/", "POST");
  messageSchema.parse(await response.json());
}

export async function currentAccount(): Promise<AccountUser | null> {
  const response = await fetch("/api/v1/auth/me/", {
    credentials: "same-origin",
    cache: "no-store",
  });
  if (response.status === 401 || response.status === 403) return null;
  if (!response.ok) throw await parseError(response);
  return sessionSchema.parse(await response.json()).user;
}

export async function updateProfile(input: {
  first_name: string;
  last_name: string;
  phone: string;
}): Promise<AccountUser> {
  const response = await mutate("/api/v1/auth/profile/", "PATCH", input);
  return sessionSchema.parse(await response.json()).user;
}

export async function verifyEmail(token: string): Promise<string> {
  const response = await mutate("/api/v1/auth/verify-email/", "POST", { token });
  return messageSchema.parse(await response.json()).message;
}

export async function resendVerification(): Promise<string> {
  const response = await mutate("/api/v1/auth/verify-email/resend/", "POST");
  return messageSchema.parse(await response.json()).message;
}

export async function requestPasswordReset(email: string): Promise<string> {
  const response = await mutate("/api/v1/auth/password-reset/", "POST", { email });
  return messageSchema.parse(await response.json()).message;
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<string> {
  const response = await mutate("/api/v1/auth/password-reset/confirm/", "POST", {
    token,
    new_password: newPassword,
  });
  return messageSchema.parse(await response.json()).message;
}
