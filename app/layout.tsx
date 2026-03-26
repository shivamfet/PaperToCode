import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PaperToCode",
  description:
    "Upload a research paper PDF and receive a comprehensive, research-grade Google Colab notebook.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main className="min-h-screen flex flex-col items-center px-4 sm:px-6 py-8 sm:py-16">
          <div className="w-full max-w-2xl">{children}</div>
        </main>
      </body>
    </html>
  );
}
