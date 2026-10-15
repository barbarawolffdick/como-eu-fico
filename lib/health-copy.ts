export const explicacoesAreas: Record<string, { resumo: string; detalhe: string }> = {
  "ATENÇÃO PRIMÁRIA": {
    resumo: "Cuidados do dia a dia, como os oferecidos nas UBS.",
    detalhe: "É a porta de entrada para muitos cuidados do SUS: por exemplo, acompanhamento de saúde na unidade básica. O valor mostra dinheiro destinado a essa área, não a quantidade de consultas realizadas.",
  },
  "ATENÇÃO DE MÉDIA E ALTA COMPLEXIDADE AMBULATORIAL E HOSPITALAR": {
    resumo: "Cuidados que exigem estrutura especializada, como exames e internações.",
    detalhe: "Média e alta complexidade são classificações do SUS para serviços que exigem profissionais, tecnologia ou estrutura especializados. O valor destinado à área não comprova quais procedimentos foram realizados.",
  },
  "ATENÇÃO ESPECIALIZADA": {
    resumo: "Cuidados com profissionais e serviços especializados.",
    detalhe: "Pode envolver, por exemplo, consultas com especialistas. Mantemos esta categoria separada de hospitais e ambulatórios porque a fonte registra grupos financeiros distintos.",
  },
  "ASSISTÊNCIA FARMACÊUTICA": {
    resumo: "Medicamentos e a organização de sua oferta à população.",
    detalhe: "Inclui ações ligadas ao acesso e ao uso de medicamentos. Dinheiro destinado a essa área não comprova, sozinho, a compra ou a entrega de um medicamento específico.",
  },
  "VIGILÂNCIA EM SAÚDE": {
    resumo: "Prevenção e acompanhamento de riscos à saúde.",
    detalhe: "Envolve ações como acompanhar doenças e prevenir riscos à população. A categoria identifica a finalidade do dinheiro, não o número de ações executadas.",
  },
  "GESTÃO DO SUS": {
    resumo: "Planejamento e organização dos serviços de saúde.",
    detalhe: "Recursos classificados pela fonte para a gestão do sistema de saúde. O valor não deve ser interpretado como número de atendimentos.",
  },
  "Estruturação da rede": {
    resumo: "Estrutura para os serviços, como obras e equipamentos.",
    detalhe: "É a finalidade registrada para o dinheiro. Não significa que uma obra foi concluída ou que um equipamento já foi comprado.",
  },
  "Manutenção dos serviços": {
    resumo: "Recursos para manter os serviços funcionando.",
    detalhe: "Também chamada de custeio: despesas do funcionamento dos serviços. A destinação do dinheiro não comprova a realização de cada despesa.",
  },
  "Operações de crédito": {
    resumo: "Recursos de empréstimos vinculados à saúde.",
    detalhe: "Indica a origem declarada dos recursos usados nas despesas, não uma transferência recebida diretamente da União.",
  },
  "Outros recursos vinculados à saúde": {
    resumo: "Outras fontes com uso destinado à saúde.",
    detalhe: "Agrupamento preservado da classificação da fonte. Não atribuímos todos esses recursos ao governo federal.",
  },
  "Impostos e transferências de impostos": {
    resumo: "Recursos de impostos arrecadados ou repartidos entre governos.",
    detalhe: "A categoria reúne recursos de impostos e transferências de impostos. Não equivale apenas à arrecadação própria da prefeitura.",
  },
  "Transferências estaduais fundo a fundo": {
    resumo: "Recursos enviados pelo estado ao fundo de saúde da cidade.",
    detalhe: "Nesta tabela, o valor é a despesa declarada com essa origem de recursos; não é o total que o estado transferiu no período.",
  },
  "Transferências federais fundo a fundo": {
    resumo: "Recursos enviados pela União ao fundo de saúde da cidade.",
    detalhe: "Nesta tabela, o valor é a despesa declarada com essa origem de recursos. Pode incluir uso de saldos anteriores; não deve ser somado aos valores recebidos do FNS.",
  },
};

export const explicacoesEquipes: Record<string, string> = {
  "eSF": "Equipe de Saúde da Família: acompanha a saúde das famílias de um território, com cuidados como consultas e acompanhamento contínuo. O número da tabela conta equipes, não profissionais ou atendimentos.",
  "eAP": "Equipe de Atenção Primária: atua nos cuidados básicos de saúde, como consultas e acompanhamento. O número da tabela conta equipes, não profissionais ou atendimentos.",
  "eMulti": "Equipe multiprofissional: reúne profissionais de diferentes áreas para atuar junto às equipes de atenção primária. A composição pode variar; a tabela não informa quantos profissionais há em cada equipe.",
};
