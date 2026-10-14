# Como Eu Fico — descrição para projeto no ChatGPT

O Como Eu Fico é um projeto de jornalismo de dados e produto digital que permite ao cidadão explorar, por município brasileiro, **como o fluxo de verba federal chega à cidade e como a cidade votou na eleição presidencial de 2026**.

A experiência coloca lado a lado a evolução temporal de benefícios, transferências, serviços e entregas federais e o resultado eleitoral municipal do primeiro turno de 2026. A pergunta é: **“Como a verba federal chega ao meu município e como ele votou?”**. O objetivo é tornar visível a presença federal no cotidiano, com linguagem simples, evidências verificáveis e comparações territoriais úteis.

O termo editorial central é **“fluxo de verba federal que impacta o município”**, e não “investimento federal” como categoria genérica. Os fluxos têm naturezas distintas: benefícios a pessoas, recursos para serviços públicos, infraestrutura e transferências a governos locais. Uma soma geral só pode ser mostrada com escopo definido, deduplicação e metodologia explícita. Verba movimentada não comprova impacto causal.

O MVP prioritário deve ser navegável e conter **TSE 2026 + Bolsa Família CGU + identificação/população municipal IBGE**, em bases independentes ligadas pelo código IBGE de sete dígitos. Outros fluxos (BPC, Pé-de-Meia, PNAE, SUS etc.) serão integrados depois. A experiência precisa nascer eleitoral e territorial, não como dashboard genérico de assistência.

GitHub público: https://github.com/barbarawolffdick/como-eu-fico
Branch de trabalho de Bolsa Família e auditorias: `feat/validar-amostra-bolsa-familia`, PR #9.
