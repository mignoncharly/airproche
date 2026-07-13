"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { Icon } from "@/components/icon";
import { trackConversion } from "@/lib/analytics";
import {
  type Airport,
  type CoverageRoute,
  type Quote,
  QuoteApiError,
  type ServiceArea,
  createQuote,
  formatMoney,
} from "@/lib/locations-pricing";

const estimatorSchema = z.object({
  trip_type: z.enum(["airport_pickup", "airport_dropoff"]),
  airport_id: z.string().uuid("SÃƒÂ©lectionnez un aÃƒÂ©roport."),
  service_area_id: z.string().uuid("SÃƒÂ©lectionnez une zone."),
  pickup_at: z.string().min(1, "Indiquez la date et lÃ¢â‚¬â„¢heure."),
  passenger_count: z.number().int().min(1, "Au moins un passager.").max(50),
  luggage_count: z.number().int().min(0).max(100),
  options: z.record(z.string(), z.number().int().min(0).max(20)),
});

type EstimatorValues = z.infer<typeof estimatorSchema>;

function localDateTime(hoursFromNow: number): string {
  const value = new Date(Date.now() + hoursFromNow * 60 * 60 * 1000);
  value.setMinutes(value.getMinutes() - value.getTimezoneOffset());
  return value.toISOString().slice(0, 16);
}

function unique<T>(values: T[]): T[] {
  return [...new Set(values)];
}

export function QuoteEstimator({
  airports,
  serviceAreas,
  routes,
  minimumLeadHours,
  maximumBookingDays,
}: {
  airports: Airport[];
  serviceAreas: ServiceArea[];
  routes: CoverageRoute[];
  minimumLeadHours: number;
  maximumBookingDays: number;
}) {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [apiError, setApiError] = useState<{ code: string; message: string } | null>(null);
  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<EstimatorValues>({
    resolver: zodResolver(estimatorSchema),
    defaultValues: {
      trip_type: "airport_pickup",
      airport_id: "",
      service_area_id: "",
      pickup_at: localDateTime(minimumLeadHours + 1),
      passenger_count: 1,
      luggage_count: 1,
      options: {},
    },
  });

  const [tripType, airportId, serviceAreaId] = useWatch({
    control,
    name: ["trip_type", "airport_id", "service_area_id"],
  });

  const availableAirportIds = useMemo(
    () => unique(routes.filter((route) => route.trip_type === tripType).map((route) => route.airport_id)),
    [routes, tripType],
  );
  const availableAirports = airports.filter((airport) => availableAirportIds.includes(airport.public_id));
  const availableAreaIds = unique(
    routes
      .filter((route) => route.trip_type === tripType && route.airport_id === airportId)
      .map((route) => route.service_area_id),
  );
  const availableAreas = serviceAreas.filter((area) => availableAreaIds.includes(area.public_id));
  const selectedRoute = routes.find(
    (route) =>
      route.trip_type === tripType &&
      route.airport_id === airportId &&
      route.service_area_id === serviceAreaId,
  );

  useEffect(() => {
    if (airportId && !availableAirportIds.includes(airportId)) {
      setValue("airport_id", "");
      setValue("service_area_id", "");
    }
  }, [airportId, availableAirportIds, setValue]);

  useEffect(() => {
    if (serviceAreaId && !availableAreaIds.includes(serviceAreaId)) {
      setValue("service_area_id", "");
    }
  }, [availableAreaIds, serviceAreaId, setValue]);

  async function submit(values: EstimatorValues) {
    setQuote(null);
    setApiError(null);
    const route = routes.find(
      (item) =>
        item.trip_type === values.trip_type &&
        item.airport_id === values.airport_id &&
        item.service_area_id === values.service_area_id,
    );
    if (!route) {
      setApiError({ code: "coverage", message: "Ce trajet nÃ¢â‚¬â„¢est pas disponible en estimation automatique." });
      return;
    }
    try {
      trackConversion("quote_started", { trip_type: values.trip_type });
      const result = await createQuote({
        trip_type: values.trip_type,
        airport_id: values.airport_id,
        service_area_id: values.service_area_id,
        pickup_at: new Date(values.pickup_at).toISOString(),
        passenger_count: values.passenger_count,
        luggage_count: values.luggage_count,
        options: route.options
          .map((option) => ({ code: option.code, quantity: values.options[option.code] ?? 0 }))
          .filter((option) => option.quantity > 0),
      });
      setQuote(result);
      trackConversion("quote_created", { trip_type: result.trip_type, currency: result.currency });
    } catch (error) {
      if (error instanceof QuoteApiError) {
        setApiError({ code: error.code, message: error.message });
      } else {
        setApiError({ code: "request_error", message: "Le service dÃ¢â‚¬â„¢estimation est momentanÃƒÂ©ment indisponible." });
      }
    }
  }

  return (
    <div className="grid gap-7 lg:grid-cols-[1.2fr_0.8fr]">
      <form className="surface-card p-6 sm:p-8" onSubmit={handleSubmit(submit)} noValidate>
        <div className="flex items-start gap-4">
          <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-700">
            <Icon name="route" className="size-5" />
          </span>
          <div>
            <h2 className="text-xl font-black tracking-tight text-slate-950">Estimer un trajet</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">Aucune coordonnÃƒÂ©e personnelle nÃ¢â‚¬â„¢est demandÃƒÂ©e ÃƒÂ  cette ÃƒÂ©tape.</p>
          </div>
        </div>

        <div className="mt-7 grid gap-5 sm:grid-cols-2">
          <label>
            <span className="form-label">Sens du trajet</span>
            <select className="form-input" {...register("trip_type")}>
              <option value="airport_pickup">De lÃ¢â‚¬â„¢aÃƒÂ©roport vers la zone</option>
              <option value="airport_dropoff">De la zone vers lÃ¢â‚¬â„¢aÃƒÂ©roport</option>
            </select>
          </label>
          <label>
            <span className="form-label">AÃƒÂ©roport</span>
            <select className="form-input" aria-invalid={Boolean(errors.airport_id)} {...register("airport_id")}>
              <option value="">SÃƒÂ©lectionner</option>
              {availableAirports.map((airport) => (
                <option key={airport.public_id} value={airport.public_id}>{airport.name} ({airport.iata_code})</option>
              ))}
            </select>
            {errors.airport_id ? <span className="form-error">{errors.airport_id.message}</span> : null}
          </label>
          <label>
            <span className="form-label">Zone desservie</span>
            <select className="form-input" disabled={!airportId} aria-invalid={Boolean(errors.service_area_id)} {...register("service_area_id")}>
              <option value="">SÃƒÂ©lectionner</option>
              {availableAreas.map((area) => <option key={area.public_id} value={area.public_id}>{area.name}</option>)}
            </select>
            {errors.service_area_id ? <span className="form-error">{errors.service_area_id.message}</span> : null}
          </label>
          <label>
            <span className="form-label">Date et heure de prise en charge</span>
            <input
              type="datetime-local"
              className="form-input"
              min={localDateTime(minimumLeadHours)}
              max={localDateTime(maximumBookingDays * 24)}
              aria-invalid={Boolean(errors.pickup_at)}
              {...register("pickup_at")}
            />
            {errors.pickup_at ? <span className="form-error">{errors.pickup_at.message}</span> : null}
          </label>
          <label>
            <span className="form-label">Passagers</span>
            <input type="number" min="1" max="50" className="form-input" {...register("passenger_count", { valueAsNumber: true })} />
            {errors.passenger_count ? <span className="form-error">{errors.passenger_count.message}</span> : null}
          </label>
          <label>
            <span className="form-label">Bagages</span>
            <input type="number" min="0" max="100" className="form-input" {...register("luggage_count", { valueAsNumber: true })} />
            {errors.luggage_count ? <span className="form-error">{errors.luggage_count.message}</span> : null}
          </label>
        </div>

        {selectedRoute?.options.length ? (
          <fieldset className="mt-7 border-t border-slate-200 pt-6">
            <legend className="text-sm font-extrabold text-slate-950">Options</legend>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {selectedRoute.options.map((option) => (
                <label key={option.code} className="rounded-xl border border-slate-200 p-4">
                  <span className="form-label">{option.label}</span>
                  <input
                    type="number"
                    min="0"
                    max={option.maximum_quantity}
                    className="form-input"
                    aria-label={`QuantitÃƒÂ© pour ${option.label}`}
                    {...register(`options.${option.code}`, { valueAsNumber: true })}
                  />
                  <span className="mt-2 block text-xs text-slate-500">Maximum : {option.maximum_quantity}</span>
                </label>
              ))}
            </div>
          </fieldset>
        ) : null}

        <button type="submit" className="button button-primary mt-7 w-full sm:w-auto" disabled={isSubmitting}>
          {isSubmitting ? "Calcul en coursÃ¢â‚¬Â¦" : "Calculer le prix"}
          {!isSubmitting ? <Icon name="arrow" className="size-4" /> : null}
        </button>
      </form>

      <aside className="surface-card h-fit p-6 sm:p-8" aria-live="polite">
        {quote ? (
          <div>
            <p className="eyebrow">Estimation serveur</p>
            <p className="mt-4 text-4xl font-black tracking-tight text-slate-950">{formatMoney(quote.total_amount, quote.currency)}</p>
            <p className="mt-2 text-sm text-slate-600">{quote.airport_iata_code} Ã‚Â· {quote.service_area_name}</p>
            <dl className="mt-6 divide-y divide-slate-200 border-y border-slate-200">
              {quote.lines.map((line) => (
                <div key={line.code} className="flex justify-between gap-4 py-3 text-sm">
                  <dt className="text-slate-600">{line.label}{line.quantity > 1 ? ` Ãƒâ€” ${line.quantity}` : ""}</dt>
                  <dd className="font-bold text-slate-950">{formatMoney(line.total_amount, quote.currency)}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-5 text-xs leading-5 text-slate-500">Devis valide jusquâ€™au {new Intl.DateTimeFormat("fr-FR", { dateStyle: "short", timeStyle: "short" }).format(new Date(quote.expires_at))}.</p><Link className="button button-primary mt-6" href={`/reservation?quote=${quote.public_id}`}>RÃ©server ce trajet</Link>
          </div>
        ) : apiError ? (
          <div>
            <span className="grid size-11 place-items-center rounded-xl bg-amber-50 text-amber-700"><Icon name="message" className="size-5" /></span>
            <h2 className="mt-5 text-xl font-black text-slate-950">VÃƒÂ©rification manuelle nÃƒÂ©cessaire</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{apiError.message}</p>
            <p className="mt-2 text-xs text-slate-500">RÃƒÂ©fÃƒÂ©rence : {apiError.code}</p>
            <Link href="/contact" className="button button-secondary mt-6">Nous contacter</Link>
          </div>
        ) : (
          <div>
            <p className="eyebrow">Prix transparent</p>
            <h2 className="mt-4 text-2xl font-black tracking-tight text-slate-950">Le montant vient uniquement du serveur.</h2>
            <p className="mt-4 text-sm leading-6 text-slate-600">Choisissez un trajet actif pour afficher son tarif et le dÃƒÂ©tail des options. La disponibilitÃƒÂ© sera de nouveau vÃƒÂ©rifiÃƒÂ©e lors de la rÃƒÂ©servation.</p>
            <ul className="mt-6 grid gap-3 text-sm font-semibold text-slate-700">
              {['Tarif fixe par trajet couvert', 'Options dÃƒÂ©taillÃƒÂ©es sÃƒÂ©parÃƒÂ©ment', 'Estimation limitÃƒÂ©e dans le temps'].map((item) => (
                <li key={item} className="flex gap-2"><Icon name="check" className="mt-0.5 size-4 shrink-0 text-emerald-700" />{item}</li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </div>
  );
}
