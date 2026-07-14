import { expect, test } from "@playwright/test";

for (const path of ["/", "/contact", "/connexion"]) {
  test(`${path} exposes a labelled, keyboard-readable document`, async ({ page }) => {
    await page.goto(path);

    await expect(page.locator("html")).toHaveAttribute("lang", "fr");
    await expect(page.locator("main")).toHaveCount(1);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("nav[aria-label=\"Navigation principale\"], nav[aria-label=\"Navigation mobile\"]").first()).toBeAttached();

    const unnamedVisibleControls = await page.locator("input, select, textarea, button").evaluateAll((elements) =>
      elements
        .filter((element) => {
          const control = element as HTMLInputElement;
          if (control.type === "hidden" || control.tabIndex < 0 || control.getClientRects().length === 0) return false;
          const hasLabel = "labels" in control && Boolean(control.labels?.length);
          return !hasLabel && !control.getAttribute("aria-label") && !control.getAttribute("aria-labelledby") && !control.textContent?.trim();
        })
        .map((element) => element.outerHTML),
    );
    expect(unnamedVisibleControls).toEqual([]);
  });
}

test("skip navigation is first in keyboard order and reaches the content", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Aller au contenu" });
  await expect(skipLink).toBeFocused();
  await expect(skipLink).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#contenu$/);
});

test("contact form fields have accessible names on mobile and desktop", async ({ page }) => {
  await page.goto("/contact");
  for (const name of ["Prénom", "Nom", "E-mail", "Téléphone", "Message"]) {
    await expect(page.getByLabel(name, { exact: true })).toBeVisible();
  }
  await expect(page.getByRole("combobox")).toBeVisible();
  await expect(page.getByRole("button", { name: /Envoyer/ })).toBeVisible();
});
