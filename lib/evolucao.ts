type Municipio = { codigo_ibge: string; vencedor: string | null; populacao: number | null };
type Detalhe = { bolsa_familia: { mes_competencia: string; valor_centavos: number | null }[] };

// Uma série incompleta não pode reduzir artificialmente o valor por habitante.
// Só publicamos a média do grupo quando todos os seus municípios têm observação.
export function evolucaoMensal(municipios: Municipio[], detalhes: Record<string, Detalhe>, meses: string[]) {
  return meses.map(mes => {
    const valores: { mes: string; "13": number | null; "22": number | null } = { mes, "13": null, "22": null };
    const cobertura: Record<string, { municipios: number; municipios_com_dado: number }> = {};
    for (const grupo of ["13", "22"] as const) {
      const cidades = municipios.filter(m => m.vencedor === grupo);
      let centavos = 0;
      let populacao = 0;
      let observados = 0;
      for (const cidade of cidades) {
        const valor = detalhes[cidade.codigo_ibge]?.bolsa_familia.find(x => x.mes_competencia === mes)?.valor_centavos;
        if (valor == null || !Number.isFinite(valor) || cidade.populacao == null || cidade.populacao <= 0) continue;
        observados++;
        centavos += valor;
        populacao += cidade.populacao;
      }
      valores[grupo] = cidades.length > 0 && observados === cidades.length && populacao > 0
        ? centavos / populacao / 100 : null;
      cobertura[grupo] = { municipios: cidades.length, municipios_com_dado: observados };
    }
    return { ...valores, cobertura };
  });
}
