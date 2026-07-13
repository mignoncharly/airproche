import { z } from "zod";

const csrfSchema = z.object({ csrf_token: z.string().min(1) });
const responseSchema = z.object({
  public_id: z.string().uuid().optional(),
  message: z.string(),
  idempotent_replay: z.boolean(),
});

export type ContactInput = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  topic: "booking" | "quote" | "payment" | "accessibility" | "other";
  message: string;
  website: string;
  form_started_at: number;
};

export class ContactApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function csrfToken(): Promise<string> {
  const response = await fetch("/api/v1/auth/csrf/", {
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) throw new ContactApiError("Le formulaire est temporairement indisponible.", response.status);
  return csrfSchema.parse(await response.json()).csrf_token;
}

export async function submitContact(input: ContactInput, idempotencyKey: string) {
  const token = await csrfToken();
  const response = await fetch("/api/v1/contact/", {
    method: "POST",
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
      "X-CSRFToken": token,
    },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new ContactApiError(
      response.status === 429
        ? "Trop de demandes ont été envoyées. Réessayez plus tard."
        : "Votre message n’a pas pu être envoyé.",
      response.status,
    );
  }
  return responseSchema.parse(await response.json());
}
