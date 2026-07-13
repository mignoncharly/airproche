import type { SVGProps } from "react";

type IconName =
  | "arrow"
  | "car"
  | "check"
  | "clock"
  | "download"
  | "home"
  | "hotel"
  | "luggage"
  | "mail"
  | "message"
  | "phone"
  | "plane"
  | "route"
  | "refresh"
  | "shield"
  | "share"
  | "users";

const paths: Record<IconName, React.ReactNode> = {
  arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
  car: <><path d="M5 17h14l-1.4-6.2A2.3 2.3 0 0 0 15.4 9H8.6a2.3 2.3 0 0 0-2.2 1.8L5 17Z" /><path d="M7 17v2m10-2v2M7.5 13h9" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  download: <><path d="M12 3v12m-5-5 5 5 5-5" /><path d="M5 21h14" /></>,
  home: <><path d="m3 11 9-7 9 7" /><path d="M5 10v10h14V10M9 20v-6h6v6" /></>,
  hotel: <><path d="M4 20V5h12v15M8 9h4m-4 4h4m-4 4h4m4-7h4v10" /></>,
  luggage: <><rect x="6" y="7" width="12" height="13" rx="2" /><path d="M9 7V5a3 3 0 0 1 6 0v2M10 11v5m4-5v5" /></>,
  mail: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m4 7 8 6 8-6" /></>,
  message: <path d="M20 15a4 4 0 0 1-4 4H9l-5 2 1.5-4A7 7 0 1 1 20 15Z" />,
  phone: <path d="M7 3h3l1.3 5-2 1.5a15 15 0 0 0 5.2 5.2l1.5-2L21 14v3c0 2.2-1.8 4-4 4A14 14 0 0 1 3 7c0-2.2 1.8-4 4-4Z" />,
  plane: <><path d="m3 11 18-7-7 17-3-7-8-3Z" /><path d="m11 14 4-4" /></>,
  refresh: <><path d="M20 7v5h-5" /><path d="M19 12a7 7 0 1 0-1.4 4.2" /></>,
  route: <><circle cx="6" cy="18" r="2" /><circle cx="18" cy="6" r="2" /><path d="M8 18h3a3 3 0 0 0 3-3v-6a3 3 0 0 1 3-3" /></>,
  shield: <path d="M12 3 4 6v5c0 5 3.4 8.4 8 10 4.6-1.6 8-5 8-10V6l-8-3Z" />,
  share: <><circle cx="18" cy="5" r="2" /><circle cx="6" cy="12" r="2" /><circle cx="18" cy="19" r="2" /><path d="m8 11 8-5m-8 7 8 5" /></>,
  users: <><circle cx="9" cy="8" r="3" /><path d="M3 20v-2a6 6 0 0 1 12 0v2" /><circle cx="17" cy="9" r="2" /><path d="M16 14a5 5 0 0 1 5 5v1" /></>,
};

export function Icon({ name, ...props }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg aria-hidden="true" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>
      {paths[name]}
    </svg>
  );
}
