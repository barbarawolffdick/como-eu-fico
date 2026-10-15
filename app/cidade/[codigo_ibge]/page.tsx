import { notFound } from "next/navigation";
import CityPage from "@/app/components/city-page";

export default async function Cidade({ params }: { params: Promise<{ codigo_ibge: string }> }) {
  const { codigo_ibge } = await params;
  if (!/^\d{7}$/.test(codigo_ibge)) notFound();
  return <CityPage key={codigo_ibge} codigo={codigo_ibge} />;
}
