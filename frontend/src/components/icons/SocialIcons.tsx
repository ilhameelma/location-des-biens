 /**
  * Icônes de réseaux sociaux — dessinées à la main en SVG minimal
  * (`currentColor`, viewBox 24x24, cohérentes avec lucide-react utilisé
  * partout ailleurs dans le projet) car lucide-react v1.x n'inclut plus
  * les logos de marques (Facebook, Instagram, LinkedIn, X...) depuis sa
  * réorganisation d'icônes.
  */
import type { SVGProps } from "react";

export function FacebookIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M13.5 21v-7.8h2.6l.4-3h-3v-1.9c0-.87.24-1.46 1.5-1.46h1.6V4.14A21 21 0 0 0 14.2 4c-2.1 0-3.6 1.28-3.6 3.63V10.2H8v3h2.6V21h2.9Z" />
    </svg>
  );
}

export function InstagramIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      {...props}
    >
      <rect x={3.5} y={3.5} width={17} height={17} rx={4.5} />
      <circle cx={12} cy={12} r={4} />
      <circle
        cx={17.2}
        cy={6.8}
        r={0.9}
        fill="currentColor"
        stroke="none"
      />
    </svg>
  );
}

export function LinkedinIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M6.94 8.5H4.1V20h2.84V8.5ZM5.52 3.5a1.65 1.65 0 1 0 0 3.3 1.65 1.65 0 0 0 0-3.3ZM20 20h-2.83v-5.87c0-1.4-.03-3.2-1.95-3.2-1.96 0-2.26 1.53-2.26 3.1V20H10.1V8.5h2.72v1.57h.04c.38-.72 1.3-1.48 2.68-1.48 2.87 0 3.4 1.89 3.4 4.35V20Z" />
    </svg>
  );
}

export function XIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M13.6 10.6 20 3.5h-2l-5.2 5.7-4-5.7H3.9l6.5 9.2-6.9 7.6h2l5.6-6.1 4.3 6.1h4.9l-6.7-9.7Zm-2 2.2-.6-.9-5.2-7.3h2.3l4.2 6 .6.9 5.4 7.6h-2.3l-4.4-6.3Z" />
    </svg>
  );
}

/**
 * Icône TikTok
 */
export function TikTokIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M19.59 7.69a4.83 4.83 0 0 1-2.82-.92 4.85 4.85 0 0 1-1.95-3.89h-3.19v13.5a2.87 2.87 0 1 1-2.87-2.87c.3 0 .6.05.87.14v-3.25a6.08 6.08 0 1 0 3.19 5.98V9.55a8.01 8.01 0 0 0 4.69 1.51V7.87c.68 0 1.37-.06 2.08-.18V7.69Z" />
    </svg>
  );
}

/**
 * Icône YouTube
 */
export function YouTubeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M23.5 6.19a3.02 3.02 0 0 0-2.12-2.14C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.38.55A3.02 3.02 0 0 0 .5 6.19 31.3 31.3 0 0 0 0 12a31.3 31.3 0 0 0 .5 5.81 3.02 3.02 0 0 0 2.12 2.14c1.88.55 9.38.55 9.38.55s7.5 0 9.38-.55a3.02 3.02 0 0 0 2.12-2.14A31.3 31.3 0 0 0 24 12a31.3 31.3 0 0 0-.5-5.81ZM9.6 15.6V8.4l6.3 3.6-6.3 3.6Z" />
    </svg>
  );
}