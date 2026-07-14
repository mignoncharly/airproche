export const primaryNavigation = [
  { href: "/chauffeurs", label: "Chauffeurs" },
  { href: "/services", label: "Services" },
  { href: "/aeroports", label: "Aéroports" },
  { href: "/fonctionnement", label: "Fonctionnement" },
  { href: "/tarifs", label: "Tarifs" },
  { href: "/a-propos", label: "À propos" },
] as const;

export const serviceHighlights = [
  {
    icon: "plane",
    title: "Accueil à l’aéroport",
    description: "Un point de rendez-vous communiqué clairement avant l’arrivée du passager.",
  },
  {
    icon: "luggage",
    title: "Aide avec les bagages",
    description: "Une prise en charge attentive, adaptée aux bagages déclarés lors de la demande.",
  },
  {
    icon: "users",
    title: "Réserver pour un proche",
    description: "Les coordonnées du voyageur restent distinctes de celles de la personne qui organise.",
  },
  {
    icon: "home",
    title: "Domicile, hôtel ou gare",
    description: "Une destination définie à l’avance pour un trajet privé, sans détour partagé.",
  },
] as const;

export const trustPoints = [
  { icon: "clock", title: "Ponctualité", description: "Un horaire et un point de rencontre confirmés." },
  { icon: "shield", title: "Sérénité", description: "Des informations claires avant chaque prise en charge." },
  { icon: "message", title: "Contact humain", description: "Un interlocuteur pour préparer le trajet." },
  { icon: "car", title: "Trajet privé", description: "Un transport organisé pour votre passager et son groupe." },
] as const;

export const processSteps = [
  { number: "01", title: "Préparez la demande", description: "Indiquez le trajet, la date et les besoins du passager." },
  { number: "02", title: "Contactez un chauffeur", description: "Votre demande est transmise sans creer de reservation." },
  { number: "03", title: "Confirmez directement", description: "Le chauffeur confirme son prix, sa disponibilite et ses conditions." },
  { number: "04", title: "Voyagez sereinement", description: "Le passager rejoint sa destination en transport privé." },
] as const;
