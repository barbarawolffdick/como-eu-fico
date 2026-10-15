// Nomes de urna do catálogo TSE 2026 usado nos snapshots publicados.
const nomes: Record<string, string> = { "13": "Lula", "14": "Renan Santos", "16": "Hertz Dias", "21": "Edmilson Costa", "22": "Flávio Bolsonaro", "27": "Clariana Barão", "29": "Rui Costa Pimenta", "30": "Zema", "35": "Veterinário Wilson Grassi", "55": "Ronaldo Caiado", "70": "Escritor Augusto Cury", "80": "Samara" };
export const nomeCandidato = (numero: string) => nomes[numero] ?? "Candidato " + numero;
