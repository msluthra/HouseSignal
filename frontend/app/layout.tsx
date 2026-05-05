import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ProphetAI",
  description: "Friendly California real estate investment advisor",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
